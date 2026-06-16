param(
    [string]$DatasetDir = "E:\yolov26\datasets\Railway Dataset",
    [string]$Prefix = "nbg",
    [int]$Groups = 16,
    [switch]$Apply
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $DatasetDir -PathType Container)) {
    throw "Dataset directory does not exist: $DatasetDir"
}

Add-Type -AssemblyName System.Drawing

$source = @"
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Linq;

public static class ImageSimilarityOrderer
{
    public sealed class Item
    {
        public string Path;
        public string Name;
        public string Extension;
        public double[] Feature;
        public int Group;
    }

    public static Item[] Load(string[] paths, int size)
    {
        Item[] items = new Item[paths.Length];
        for (int i = 0; i < paths.Length; i++)
        {
            items[i] = new Item
            {
                Path = paths[i],
                Name = System.IO.Path.GetFileName(paths[i]),
                Extension = System.IO.Path.GetExtension(paths[i]).ToLowerInvariant(),
                Feature = ExtractFeature(paths[i], size),
                Group = -1
            };
        }
        return items;
    }

    public static int[] Order(Item[] items, int requestedGroups)
    {
        if (items.Length == 0) return new int[0];
        int k = Math.Max(1, Math.Min(requestedGroups, items.Length));
        int dim = items[0].Feature.Length;
        double[][] centroids = SeedCentroids(items, k, dim);

        for (int iter = 0; iter < 24; iter++)
        {
            bool changed = false;
            for (int i = 0; i < items.Length; i++)
            {
                int best = Nearest(items[i].Feature, centroids);
                if (items[i].Group != best)
                {
                    items[i].Group = best;
                    changed = true;
                }
            }

            centroids = RecomputeCentroids(items, k, dim, centroids);
            if (!changed && iter > 2) break;
        }

        int[] groupOrder = OrderVectors(centroids, null, FarthestFromMean(centroids));
        List<int> output = new List<int>(items.Length);
        double[] previous = null;

        foreach (int group in groupOrder)
        {
            List<int> indexes = new List<int>();
            for (int i = 0; i < items.Length; i++)
            {
                if (items[i].Group == group) indexes.Add(i);
            }
            if (indexes.Count == 0) continue;

            double[][] vectors = indexes.Select(i => items[i].Feature).ToArray();
            int start = previous == null ? FarthestFromMean(vectors) : Nearest(previous, vectors);
            int[] localOrder = OrderVectors(vectors, previous, start);

            foreach (int local in localOrder)
            {
                int itemIndex = indexes[local];
                output.Add(itemIndex);
                previous = items[itemIndex].Feature;
            }
        }

        return output.ToArray();
    }

    private static double[] ExtractFeature(string path, int size)
    {
        using (Bitmap src = (Bitmap)Image.FromFile(path))
        using (Bitmap thumb = new Bitmap(size, size))
        using (Graphics g = Graphics.FromImage(thumb))
        {
            g.InterpolationMode = InterpolationMode.HighQualityBicubic;
            g.SmoothingMode = SmoothingMode.HighQuality;
            g.PixelOffsetMode = PixelOffsetMode.HighQuality;
            g.DrawImage(src, 0, 0, size, size);

            double[] feature = new double[size * size * 4 + 4];
            int idx = 0;
            double meanR = 0.0, meanG = 0.0, meanB = 0.0, meanY = 0.0;

            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    Color c = thumb.GetPixel(x, y);
                    double r = c.R / 255.0;
                    double gr = c.G / 255.0;
                    double b = c.B / 255.0;
                    double luma = 0.299 * r + 0.587 * gr + 0.114 * b;

                    feature[idx++] = r;
                    feature[idx++] = gr;
                    feature[idx++] = b;
                    feature[idx++] = luma;

                    meanR += r;
                    meanG += gr;
                    meanB += b;
                    meanY += luma;
                }
            }

            double pixels = size * size;
            feature[idx++] = meanR / pixels;
            feature[idx++] = meanG / pixels;
            feature[idx++] = meanB / pixels;
            feature[idx++] = meanY / pixels;

            return feature;
        }
    }

    private static double[][] SeedCentroids(Item[] items, int k, int dim)
    {
        double[] mean = Mean(items.Select(i => i.Feature).ToArray(), dim);
        double[][] centroids = new double[k][];
        centroids[0] = (double[])items[Farthest(items.Select(i => i.Feature).ToArray(), mean)].Feature.Clone();

        for (int c = 1; c < k; c++)
        {
            int bestIndex = 0;
            double bestDistance = -1.0;
            for (int i = 0; i < items.Length; i++)
            {
                double nearest = double.MaxValue;
                for (int j = 0; j < c; j++)
                {
                    nearest = Math.Min(nearest, Distance(items[i].Feature, centroids[j]));
                }
                if (nearest > bestDistance)
                {
                    bestDistance = nearest;
                    bestIndex = i;
                }
            }
            centroids[c] = (double[])items[bestIndex].Feature.Clone();
        }

        return centroids;
    }

    private static double[][] RecomputeCentroids(Item[] items, int k, int dim, double[][] oldCentroids)
    {
        double[][] sums = new double[k][];
        int[] counts = new int[k];
        for (int i = 0; i < k; i++) sums[i] = new double[dim];

        foreach (Item item in items)
        {
            int group = item.Group;
            counts[group]++;
            for (int d = 0; d < dim; d++) sums[group][d] += item.Feature[d];
        }

        for (int group = 0; group < k; group++)
        {
            if (counts[group] == 0)
            {
                sums[group] = (double[])oldCentroids[group].Clone();
                continue;
            }
            for (int d = 0; d < dim; d++) sums[group][d] /= counts[group];
        }

        return sums;
    }

    private static int[] OrderVectors(double[][] vectors, double[] previous, int start)
    {
        int n = vectors.Length;
        bool[] used = new bool[n];
        int[] order = new int[n];
        int current = start;

        for (int outIndex = 0; outIndex < n; outIndex++)
        {
            order[outIndex] = current;
            used[current] = true;

            if (outIndex == n - 1) break;

            int best = -1;
            double bestDistance = double.MaxValue;
            for (int i = 0; i < n; i++)
            {
                if (used[i]) continue;
                double distance = Distance(vectors[current], vectors[i]);
                if (distance < bestDistance)
                {
                    bestDistance = distance;
                    best = i;
                }
            }
            current = best;
        }

        return order;
    }

    private static int FarthestFromMean(double[][] vectors)
    {
        if (vectors.Length == 1) return 0;
        double[] mean = Mean(vectors, vectors[0].Length);
        return Farthest(vectors, mean);
    }

    private static int Farthest(double[][] vectors, double[] target)
    {
        int best = 0;
        double bestDistance = -1.0;
        for (int i = 0; i < vectors.Length; i++)
        {
            double distance = Distance(vectors[i], target);
            if (distance > bestDistance)
            {
                bestDistance = distance;
                best = i;
            }
        }
        return best;
    }

    private static int Nearest(double[] vector, double[][] candidates)
    {
        int best = 0;
        double bestDistance = double.MaxValue;
        for (int i = 0; i < candidates.Length; i++)
        {
            double distance = Distance(vector, candidates[i]);
            if (distance < bestDistance)
            {
                bestDistance = distance;
                best = i;
            }
        }
        return best;
    }

    private static double[] Mean(double[][] vectors, int dim)
    {
        double[] mean = new double[dim];
        foreach (double[] vector in vectors)
        {
            for (int d = 0; d < dim; d++) mean[d] += vector[d];
        }
        for (int d = 0; d < dim; d++) mean[d] /= vectors.Length;
        return mean;
    }

    private static double Distance(double[] a, double[] b)
    {
        double sum = 0.0;
        for (int i = 0; i < a.Length; i++)
        {
            double diff = a[i] - b[i];
            sum += diff * diff;
        }
        return sum;
    }
}
"@

Add-Type -TypeDefinition $source -ReferencedAssemblies "System.Drawing"

$imageExtensions = @(".jpg", ".jpeg", ".png", ".bmp")
$files = Get-ChildItem -LiteralPath $DatasetDir -File |
    Where-Object { $imageExtensions -contains $_.Extension.ToLowerInvariant() } |
    Sort-Object Name

if ($files.Count -eq 0) {
    throw "No image files found in: $DatasetDir"
}

if ($Groups -lt 1) {
    throw "Groups must be at least 1."
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$featureSize = 12
$items = [ImageSimilarityOrderer]::Load([string[]]$files.FullName, $featureSize)
$order = [ImageSimilarityOrderer]::Order($items, $Groups)

$rows = New-Object System.Collections.Generic.List[object]
$seenTargets = @{}

for ($i = 0; $i -lt $order.Length; $i++) {
    $item = $items[$order[$i]]
    $sequence = $i + 1
    $newName = "{0}_{1}{2}" -f $Prefix, $sequence, $item.Extension
    $targetKey = $newName.ToLowerInvariant()

    if ($seenTargets.ContainsKey($targetKey)) {
        throw "Duplicate target name generated: $newName"
    }
    $seenTargets[$targetKey] = $true

    $tempName = "__${Prefix}_tmp_${timestamp}_${sequence}$($item.Extension)"
    $rows.Add([pscustomobject]@{
        sequence = $sequence
        group = $item.Group
        old_name = $item.Name
        new_name = $newName
        temp_name = $tempName
        old_path = $item.Path
        new_path = (Join-Path $DatasetDir $newName)
    })
}

$mode = if ($Apply) { "applied" } else { "dryrun" }
$mappingPath = Join-Path $DatasetDir ("rename_mapping_{0}_{1}_{2}.csv" -f $Prefix, $mode, $timestamp)
$rows | Export-Csv -LiteralPath $mappingPath -NoTypeInformation -Encoding UTF8

Write-Output ("Images: {0}" -f $files.Count)
Write-Output ("Groups: {0}" -f ([Math]::Min($Groups, $files.Count)))
Write-Output ("Mapping: {0}" -f $mappingPath)
Write-Output "Preview:"
$rows | Select-Object -First 12 sequence,group,old_name,new_name | Format-Table -AutoSize | Out-String | Write-Output

if (-not $Apply) {
    Write-Output "Dry run only. Re-run with -Apply to rename files."
    exit 0
}

foreach ($row in $rows) {
    $tempPath = Join-Path $DatasetDir $row.temp_name
    if (Test-Path -LiteralPath $tempPath) {
        throw "Temporary file already exists: $tempPath"
    }
}

foreach ($row in $rows) {
    Rename-Item -LiteralPath $row.old_path -NewName $row.temp_name
}

foreach ($row in $rows) {
    $tempPath = Join-Path $DatasetDir $row.temp_name
    Rename-Item -LiteralPath $tempPath -NewName $row.new_name
}

Write-Output "Rename complete."
