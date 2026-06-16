# YOLO 人员检测训练结果说明

本文档说明这个训练结果目录里的文件分别是什么、图片里的指标怎么看，以及下一步应该如何验证模型。

训练结果目录：

```text
E:\yolov26\runs\detect\person_yolo26n_768_b8
```

当前最佳模型：

```text
E:\yolov26\runs\detect\person_yolo26n_768_b8\weights\best.pt
```

## 1. 本次训练概况

本次训练任务：

```text
任务类型：目标检测 detect
检测类别：person
模型：YOLO26n
输入尺寸：768
batch：8
训练轮数：80
数据集：E:\yolov26\datasets\railway_person_yolo
```

最终验证指标：

```text
Precision:  0.9902
Recall:     0.9954
mAP50:      0.9944
mAP50-95:   0.7414
```

简单结论：

```text
模型在当前铁路人员验证集上表现很好。
数据集格式、训练流程、GPU 使用都没有问题。
```

但要注意：

```text
这个结果只能证明模型在同来源验证集上表现好。
还不能直接证明它能适应所有铁路场景、普通行人、夜晚、雨天、站台、不同摄像头角度。
```

## 2. 目录里的文件是什么意思

### `weights/`

模型权重目录。

里面通常有：

```text
best.pt
last.pt
```

### `weights/best.pt`

训练过程中验证效果最好的模型。

后续预测、测试、导出、部署，一般都用它。

使用示例：

```powershell
yolo detect predict model=E:\yolov26\runs\detect\person_yolo26n_768_b8\weights\best.pt source=你的图片或视频 device=0
```

### `weights/last.pt`

最后一轮训练结束时保存的模型。

如果你想接着训练，可以用它继续。

例如：

```powershell
yolo detect train model=E:\yolov26\runs\detect\person_yolo26n_768_b8\weights\last.pt data=E:\yolov26\datasets\railway_person_yolo\data.yaml epochs=20 imgsz=768 batch=8 device=0
```

日常测试优先用：

```text
best.pt
```

### `args.yaml`

记录本次训练使用过的全部参数。

它能回答：

```text
用的是哪个模型？
用的是哪个数据集？
训练了多少轮？
图片尺寸是多少？
batch 是多少？
用的是 CPU 还是 GPU？
数据增强参数是什么？
```

如果以后你要复现实验，或者对比两次训练，这个文件很重要。

### `results.csv`

每一轮训练的详细指标表格。

重要列包括：

```text
epoch
train/box_loss
train/cls_loss
train/dfl_loss
val/box_loss
val/cls_loss
val/dfl_loss
metrics/precision(B)
metrics/recall(B)
metrics/mAP50(B)
metrics/mAP50-95(B)
```

你最后一轮的结果：

```text
epoch:                80
train/box_loss:       0.80795
train/cls_loss:       0.25179
train/dfl_loss:       0.00179
val/box_loss:         0.92970
val/cls_loss:         0.23842
val/dfl_loss:         0.00297
precision:            0.99022
recall:               0.99540
mAP50:                0.99439
mAP50-95:             0.74140
```

### `results.png`

训练曲线图。

这是最常看的总览图片。

里面包含：

```text
train/box_loss
train/cls_loss
train/dfl_loss
val/box_loss
val/cls_loss
val/dfl_loss
metrics/precision(B)
metrics/recall(B)
metrics/mAP50(B)
metrics/mAP50-95(B)
```

怎么看：

```text
好的情况：
- train loss 下降
- val loss 下降或稳定
- precision 上升并稳定
- recall 上升并稳定
- mAP50 上升并稳定
- mAP50-95 上升并稳定

不好的情况：
- train loss 下降，但 val loss 明显上升，可能过拟合
- precision 高但 recall 低，说明误检少但漏检多
- recall 高但 precision 低，说明漏检少但误检多
- mAP 一开始升，后面突然崩掉
- 曲线长期剧烈波动
```

你这次的曲线属于健康情况。

## 3. 核心指标怎么理解

### Precision 精确率

意思是：

```text
模型框出来的人里面，有多少是真的人？
```

你的结果：

```text
Precision = 0.9902
```

说明：

```text
在验证集上，模型把非人误检成人的情况很少。
```

### Recall 召回率

意思是：

```text
真实存在的人里面，模型找到了多少？
```

你的结果：

```text
Recall = 0.9954
```

说明：

```text
在验证集上，模型漏检的人很少。
```

### mAP50

`mAP50` 是在 IoU=0.50 标准下的平均精度。

IoU 可以理解为：

```text
预测框和真实框重叠得有多好。
```

你的结果：

```text
mAP50 = 0.9944
```

说明：

```text
在相对宽松的框重叠标准下，检测效果非常好。
```

### mAP50-95

`mAP50-95` 比 `mAP50` 严格得多。

它会从 IoU=0.50 一直评估到 IoU=0.95。

你的结果：

```text
mAP50-95 = 0.7414
```

说明：

```text
模型能稳定找到人，但在非常严格的框位置要求下，框还不算完美。
```

铁路监控画面里人通常比较小、比较远，所以 `mAP50-95` 比 `mAP50` 低是正常的。

## 4. Loss 怎么看

### `box_loss`

框位置损失。

越低越好。

下降说明模型越来越会画框。

### `cls_loss`

分类损失。

你现在只有一个类别：

```text
person
```

所以这个值下降，说明模型越来越确定目标是 person。

### `dfl_loss`

更细的框回归损失。

你可以简单理解为：

```text
另一个和框精度有关的 loss。
```

越低越好。

## 5. 几张曲线图怎么看

### `BoxF1_curve.png`

F1 曲线。

F1 是 Precision 和 Recall 的综合平衡。

它可以帮你选择预测时的 `conf` 阈值。

如果你想少漏检：

```text
conf 可以低一点，比如 0.15 或 0.20
```

如果你想少误报：

```text
conf 可以高一点，比如 0.35 或 0.40
```

默认可以先用：

```text
conf=0.25
```

### `BoxPR_curve.png`

Precision-Recall 曲线。

好的曲线应该尽量靠右上方。

说明：

```text
模型可以同时保持较高精确率和较高召回率。
```

### `BoxP_curve.png`

Precision 随 confidence 阈值变化的曲线。

一般来说：

```text
conf 越高，模型越谨慎，误检越少。
```

### `BoxR_curve.png`

Recall 随 confidence 阈值变化的曲线。

一般来说：

```text
conf 越高，模型越谨慎，但漏检可能增加。
```

所以实际使用时要取平衡。

铁路安全检测里，通常漏检比误报更危险，所以不要把 `conf` 调得太高。

## 6. 混淆矩阵怎么看

### `confusion_matrix.png`

混淆矩阵。

你现在只有一个类别，所以主要看：

```text
person 是否被识别成 person
person 是否被漏成 background
background 是否被误检成 person
```

### `confusion_matrix_normalized.png`

归一化后的混淆矩阵。

它更适合看比例。

## 7. 标签图和预测图怎么看

### `labels.jpg`

标签分布图。

它可以帮你检查：

```text
框是不是集中在某些位置？
框是不是都很小？
有没有异常大框或异常小框？
标注分布是否奇怪？
```

### `train_batch0.jpg`

训练样本图。

看它是为了确认：

```text
训练图片是否正常读取
标签框是否框在人身上
数据增强后是否仍然合理
```

### `val_batch0_labels.jpg`

验证集真实标签图。

这张图表示：

```text
数据集认为哪里有人。
```

### `val_batch0_pred.jpg`

模型预测图。

这张图表示：

```text
模型认为哪里有人。
```

你应该把这两张对应起来看：

```text
val_batch0_labels.jpg
val_batch0_pred.jpg
```

重点检查：

```text
有没有漏掉人？
有没有把非人框成人？
框是否明显偏移？
一个人有没有被重复框？
远处小人能不能识别？
```

## 8. 如何验证模型

可以随便传几张照片让模型识别吗？

可以。

但要区分两种验证：

```text
随便找几张图片测试 = 定性测试
准备一组代表性测试集 = 更可靠的验证
```

### 8.1 随便找几张图测试

你可以新建一个目录：

```text
E:\yolov26\test_images\person_test
```

把几张图片放进去，例如：

```text
railway_001.jpg
railway_002.jpg
person_001.jpg
no_person_001.jpg
```

然后运行：

```powershell
yolo detect predict model=E:\yolov26\runs\detect\person_yolo26n_768_b8\weights\best.pt source=E:\yolov26\test_images\person_test conf=0.25 imgsz=768 device=0 name=person_manual_test
```

输出会保存在：

```text
E:\yolov26\runs\detect\person_manual_test
```

你打开输出图片看框就行。

这种测试能快速回答：

```text
模型能不能跑？
大概能不能识别人？
有没有明显误检？
```

但它不能严谨证明模型很好，因为图片数量太少。

### 8.2 更可靠的验证方法

建议准备一个外部测试集。

目录可以这样：

```text
E:\yolov26\test_images\external_person_test
```

里面放：

```text
1. 铁路场景里有人
2. 铁路场景里没人
3. 普通行人
4. 工人
5. 远处小人
6. 站台或轨道旁的人
7. 复杂背景
8. 光照变化
```

建议数量：

```text
至少 50 张
最好 100-300 张
```

测试命令：

```powershell
yolo detect predict model=E:\yolov26\runs\detect\person_yolo26n_768_b8\weights\best.pt source=E:\yolov26\test_images\external_person_test conf=0.25 imgsz=768 device=0 name=person_external_test_conf025
```

然后你人工统计：

```text
漏检了多少人？
误检了多少非人？
小目标表现怎么样？
普通行人表现怎么样？
铁路工人表现怎么样？
无人图片是否乱报？
```

### 8.3 如果你想得到正式指标

如果你想得到 Precision、Recall、mAP 这些正式指标，那么测试图片也必须有标签。

也就是说，你需要为外部测试图片准备 YOLO 标注：

```text
images/test
labels/test
```

然后在 `data.yaml` 里加：

```yaml
test: images/test
```

再运行：

```powershell
yolo detect val model=E:\yolov26\runs\detect\person_yolo26n_768_b8\weights\best.pt data=E:\yolov26\datasets\railway_person_yolo\data.yaml split=val imgsz=768 device=0
```

如果你做了独立 test 集，就用：

```powershell
yolo detect val model=E:\yolov26\runs\detect\person_yolo26n_768_b8\weights\best.pt data=你的测试集data.yaml split=test imgsz=768 device=0
```

没有标签时，只能看预测图片，不能计算 mAP。

## 9. 判断模型好坏的实用标准

对于你的铁路人员检测任务，可以这样判断：

```text
第一层：能不能正常识别人
第二层：远处小人能不能识别
第三层：普通行人能不能识别
第四层：没有人的铁路图片会不会误报
第五层：换摄像头、换天气、换场景是否还能识别
```

如果外部测试时：

```text
漏检多
```

可以尝试：

```text
降低 conf
补充更多类似漏检场景的数据
增加普通 person 数据
训练更久或使用更大模型
```

如果外部测试时：

```text
误检多
```

可以尝试：

```text
提高 conf
加入更多无人铁路背景图作为负样本
人工清理错误标签
补充复杂背景图片
```

## 10. 当前结论

当前模型：

```text
E:\yolov26\runs\detect\person_yolo26n_768_b8\weights\best.pt
```

可以作为你的第一版铁路人员检测模型。

它已经在同来源验证集上表现很好。

下一步不是继续盲目训练，而是：

```text
找外部图片测试
记录漏检和误检
根据错误类型决定是否补数据
```

推荐先做：

```text
20-50 张手动图片测试
```

如果效果看起来正常，再做：

```text
100-300 张外部测试集
```
