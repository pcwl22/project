import os
from typing import List, Tuple, Dict
import cv2
import numpy as np
from ultralytics import YOLO
from ..config import settings


class YoloService:
    """
    YOLO检测服务
    提供商品检测和空货架推算功能
    """
    _model = None
    _current_model_path = None

    @classmethod
    def load_model(cls, model_path: str = None):
        """
        加载YOLO模型（支持动态切换模型）
        
        Args:
            model_path: 模型文件路径，如果为 None 则使用默认模型
        """
        # 如果没有指定模型路径，使用默认模型
        if model_path is None:
            model_path = settings.yolo_weights
        
        # 如果指定的是文件名（不是完整路径），则在 model_dir 中查找
        if not os.path.isabs(model_path) and not os.path.exists(model_path):
            model_path = os.path.join(settings.model_dir, model_path)
        
        # 如果模型路径改变了，重新加载模型
        if cls._model is None or cls._current_model_path != model_path:
            print(f"加载模型: {model_path}")
            cls._model = YOLO(model_path)
            cls._current_model_path = model_path
        
        return cls._model

    @classmethod
    def _calculate_iou(cls, box1: List[float], box2: List[float]) -> float:
        """
        计算两个检测框的 IoU (Intersection over Union)
        
        Args:
            box1: [label, x1, y1, x2, y2, score] 或 [x1, y1, x2, y2]
            box2: [label, x1, y1, x2, y2, score] 或 [x1, y1, x2, y2]
            
        Returns:
            IoU 值 (0-1)
        """
        # 提取坐标（兼容不同格式）
        if len(box1) == 6:
            _, x1_1, y1_1, x2_1, y2_1, _ = box1
        else:
            x1_1, y1_1, x2_1, y2_1 = box1
            
        if len(box2) == 6:
            _, x1_2, y1_2, x2_2, y2_2, _ = box2
        else:
            x1_2, y1_2, x2_2, y2_2 = box2
        
        # 计算交集区域
        x1_inter = max(x1_1, x1_2)
        y1_inter = max(y1_1, y1_2)
        x2_inter = min(x2_1, x2_2)
        y2_inter = min(y2_1, y2_2)
        
        # 如果没有交集
        if x2_inter < x1_inter or y2_inter < y1_inter:
            return 0.0
        
        # 计算交集面积
        inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)
        
        # 计算两个框的面积
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        
        # 计算并集面积
        union_area = box1_area + box2_area - inter_area
        
        # 计算 IoU
        iou = inter_area / union_area if union_area > 0 else 0.0
        
        return iou
    
    @classmethod
    def _remove_overlapping_empty_shelves(cls, detected_items: List[List], iou_threshold: float = 0.1) -> List[List]:
        """
        移除与商品检测框重叠的空货架检测框
        商品检测框优先级高于空货架检测框
        
        Args:
            detected_items: 所有检测结果 [[label, x1, y1, x2, y2, score], ...]
            iou_threshold: IoU 阈值，超过此值认为重叠
            
        Returns:
            去重后的检测结果
        """
        # 分离商品和空货架
        products = [item for item in detected_items if item[0] != "empty_shelf"]
        empty_shelves = [item for item in detected_items if item[0] == "empty_shelf"]
        
        # 如果没有空货架，直接返回
        if not empty_shelves:
            return detected_items
        
        # 过滤掉与商品重叠的空货架
        filtered_empty_shelves = []
        for empty_shelf in empty_shelves:
            is_overlapping = False
            
            # 检查是否与任何商品重叠
            for product in products:
                iou = cls._calculate_iou(empty_shelf, product)
                if iou > iou_threshold:
                    is_overlapping = True
                    break
            
            # 如果不重叠，保留该空货架
            if not is_overlapping:
                filtered_empty_shelves.append(empty_shelf)
        
        # 返回商品 + 过滤后的空货架
        return products + filtered_empty_shelves

    @classmethod
    def _filter_black_edge_detections(cls, detected_items: List[List], image, img_width: int, img_height: int) -> List[List]:
        """
        过滤掉黑边区域的检测框（上下左右四个边缘）
        
        Args:
            detected_items: 检测项列表
            image: 原始图片
            img_width: 图片宽度
            img_height: 图片高度
            
        Returns:
            过滤后的检测项列表
        """
        if image is None:
            return detected_items
        
        filtered_items = []
        removed_count = 0
        
        for item in detected_items:
            label, x1, y1, x2, y2, score = item
            
            # 计算检测框的中心点
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            is_in_black_edge = False
            
            # 检查是否在左边缘黑边区域
            if center_x < img_width * 0.2:  # 左侧20%区域
                if x1 > 0:
                    edge_region = image[int(y1):int(y2), 0:int(x1)]
                    if edge_region.size > 0 and edge_region.mean() < settings.black_edge_threshold:
                        is_in_black_edge = True
            
            # 检查是否在右边缘黑边区域
            if not is_in_black_edge and center_x > img_width * 0.8:  # 右侧20%区域
                if x2 < img_width:
                    edge_region = image[int(y1):int(y2), int(x2):img_width]
                    if edge_region.size > 0 and edge_region.mean() < settings.black_edge_threshold:
                        is_in_black_edge = True
            
            # 检查是否在上边缘黑边区域
            if not is_in_black_edge and center_y < img_height * 0.2:  # 上侧20%区域
                if y1 > 0:
                    edge_region = image[0:int(y1), int(x1):int(x2)]
                    if edge_region.size > 0 and edge_region.mean() < settings.black_edge_threshold:
                        is_in_black_edge = True
            
            # 检查是否在下边缘黑边区域
            if not is_in_black_edge and center_y > img_height * 0.8:  # 下侧20%区域
                if y2 < img_height:
                    edge_region = image[int(y2):img_height, int(x1):int(x2)]
                    if edge_region.size > 0 and edge_region.mean() < settings.black_edge_threshold:
                        is_in_black_edge = True
            
            # 如果不在黑边区域，保留该检测框
            if not is_in_black_edge:
                filtered_items.append(item)
            else:
                removed_count += 1
        
        if removed_count > 0:
            print(f"  - 过滤黑边区域的检测框: {removed_count} 个")
        
        return filtered_items

    @classmethod
    def _cluster_into_rows(cls, items: List[List], avg_height: float) -> List[List[List]]:
        """
        将检测到的商品按垂直位置聚类成行
        
        Args:
            items: 商品列表 [[label, x1, y1, x2, y2, score], ...]
            avg_height: 平均商品高度
            
        Returns:
            行列表，每行包含该行的所有商品
        """
        if not items:
            return []
        
        # 按 Y 坐标中心点排序
        items_sorted = sorted(items, key=lambda x: (x[2] + x[4]) / 2)
        
        rows = []
        current_row = [items_sorted[0]]
        
        for i in range(1, len(items_sorted)):
            cur_y_center = (items_sorted[i][2] + items_sorted[i][4]) / 2
            last_y_center = (current_row[-1][2] + current_row[-1][4]) / 2
            
            # 如果垂直距离小于阈值，视为同一行
            if abs(cur_y_center - last_y_center) < avg_height * settings.row_threshold:
                current_row.append(items_sorted[i])
            else:
                rows.append(current_row)
                current_row = [items_sorted[i]]
        
        rows.append(current_row)
        return rows

    @classmethod
    def _detect_gaps_in_row(cls, row: List[List], avg_width: float, img_width: int, image=None) -> List[List]:
        """
        检测一行中的空位
        
        Args:
            row: 该行的商品列表
            avg_width: 平均商品宽度
            img_width: 图片宽度
            image: 原始图片（用于检测黑边）
            
        Returns:
            空货架列表 [[label, x1, y1, x2, y2, score], ...]
        """
        empty_shelves = []
        
        # 按 X 坐标排序
        row_sorted = sorted(row, key=lambda x: x[1])
        
        # 计算该行的 Y 坐标范围
        row_y1 = min(item[2] for item in row_sorted)
        row_y2 = max(item[4] for item in row_sorted)
        
        # 检测商品之间的间隙
        for i in range(len(row_sorted) - 1):
            left_item = row_sorted[i]
            right_item = row_sorted[i + 1]
            
            gap_start = left_item[3]  # 左侧商品的右边界
            gap_end = right_item[1]   # 右侧商品的左边界
            gap_width = gap_end - gap_start
            
            # 判断是否为空位
            threshold = max(avg_width * settings.gap_threshold, settings.min_gap_pixels)
            if gap_width > threshold:
                # 创建空货架框（算法推算的空货架，置信度设为 -1.0 表示非模型检测）
                empty_shelf = [
                    "empty_shelf",
                    gap_start,
                    row_y1,
                    gap_end,
                    row_y2,
                    -1.0  # 算法推算的空货架不需要置信度
                ]
                empty_shelves.append(empty_shelf)
        
        # 检测货架边缘的空位（可选）
        if settings.edge_detection and len(row_sorted) >= settings.min_products_per_row:
            # 左边缘空位
            left_edge_gap = row_sorted[0][1]  # 第一个商品的左边界
            if left_edge_gap > avg_width * settings.gap_threshold:
                # 检查左边缘是否为黑边
                is_black_edge = False
                if image is not None:
                    # 采样左边缘区域的像素值
                    edge_region = image[int(row_y1):int(row_y2), 0:int(row_sorted[0][1])]
                    if edge_region.size > 0:
                        mean_brightness = edge_region.mean()
                        # 如果平均亮度低于阈值，认为是黑边
                        if mean_brightness < settings.black_edge_threshold:
                            is_black_edge = True
                
                if not is_black_edge:
                    empty_shelf = [
                        "empty_shelf",
                        0,
                        row_y1,
                        row_sorted[0][1],
                        row_y2,
                        -1.0  # 算法推算的空货架不需要置信度
                    ]
                    empty_shelves.append(empty_shelf)
            
            # 右边缘空位
            right_edge_gap = img_width - row_sorted[-1][3]  # 图片宽度 - 最后一个商品的右边界
            if right_edge_gap > avg_width * settings.gap_threshold:
                # 检查右边缘是否为黑边
                is_black_edge = False
                if image is not None:
                    # 采样右边缘区域的像素值
                    edge_region = image[int(row_y1):int(row_y2), int(row_sorted[-1][3]):img_width]
                    if edge_region.size > 0:
                        mean_brightness = edge_region.mean()
                        # 如果平均亮度低于阈值，认为是黑边
                        if mean_brightness < settings.black_edge_threshold:
                            is_black_edge = True
                
                if not is_black_edge:
                    empty_shelf = [
                        "empty_shelf",
                        row_sorted[-1][3],
                        row_y1,
                        img_width,
                        row_y2,
                        -1.0  # 算法推算的空货架不需要置信度
                    ]
                    empty_shelves.append(empty_shelf)
        
        return empty_shelves

    @classmethod
    def _calculate_statistics(cls, items: List[List]) -> Dict:
        """
        计算检测统计信息
        
        Args:
            items: 所有检测项（商品+空货架）
            
        Returns:
            统计信息字典
        """
        product_count = sum(1 for item in items if item[0] != "empty_shelf")
        empty_count = sum(1 for item in items if item[0] == "empty_shelf")
        total_slots = product_count + empty_count
        
        return {
            "product_count": product_count,
            "empty_count": empty_count,
            "total_slots": total_slots,
            "empty_rate": empty_count / total_slots if total_slots > 0 else 0
        }

    @classmethod
    def predict_on_image(cls, image_path: str, save_dir: str, conf_threshold: float = 0.25,
                         iou_threshold: float = 0.45, model_path: str = None) -> Tuple[
        str, List[Tuple[str, float, float, float, float, float]]]:
        """
        对图片进行检测，包括商品检测和空货架推算
        
        算法流程：
        1. 使用YOLO模型检测商品
        2. 将商品按垂直位置聚类成行
        3. 在每行中检测商品之间的间隙
        4. 当间隙超过阈值时，推算为空货架
        5. 绘制可视化结果并保存
        
        Args:
            image_path: 图片路径
            save_dir: 保存目录
            conf_threshold: 置信度阈值
            iou_threshold: IOU 阈值
            model_path: 模型文件路径（可选，如果为 None 则使用默认模型）
            
        Returns:
            (保存路径, 检测结果列表)
        """
        model = cls.load_model(model_path)
        os.makedirs(save_dir, exist_ok=True)

        # 1. 执行 YOLO 商品检测
        results = model.predict(
            source=image_path, 
            conf=conf_threshold, 
            iou=iou_threshold, 
            save=False, 
            verbose=False,
            stream=False  # 单张图片不需要 stream
        )
        
        if not results:
            raise ValueError("No result returned by model")

        r = results[0]
        img = r.orig_img.copy()
        img_height, img_width = img.shape[:2]
        
        boxes_raw = r.boxes.xyxy.cpu().numpy()
        scores_raw = r.boxes.conf.cpu().numpy()
        classes_raw = r.boxes.cls.cpu().numpy()
        names = model.names

        # 2. 整理检测到的商品和模型检测的空货架
        detected_items = []
        model_detected_empty_shelves = []  # 记录模型直接检测的空货架
        
        print(f"\n{'='*70}")
        print(f"图片检测 - {os.path.basename(image_path)}")
        print(f"{'='*70}")
        print(f"置信度阈值: {conf_threshold}, IOU阈值: {iou_threshold}")
        
        for b, s, c in zip(boxes_raw, scores_raw, classes_raw):
            x1, y1, x2, y2 = map(float, b.tolist())
            class_name = names[int(c)]
            confidence = float(s)
            
            # 如果模型本身检测到空货架，保留其置信度
            # 支持的关键字：empty, 空, missing, vacant, gap, 缺货
            empty_keywords = ["empty", "空", "missing", "vacant", "gap", "缺货"]
            if any(keyword in class_name.lower() for keyword in empty_keywords):
                detected_items.append([class_name, x1, y1, x2, y2, confidence])
                model_detected_empty_shelves.append([class_name, x1, y1, x2, y2, confidence])
            else:
                detected_items.append([class_name, x1, y1, x2, y2, confidence])
        
        print(f"\n模型检测结果:")
        print(f"  - 总检测数: {len(detected_items)}")
        print(f"  - 商品数: {len(detected_items) - len(model_detected_empty_shelves)}")
        print(f"  - 模型检测的空货架: {len(model_detected_empty_shelves)}")
        
        # 2.5 过滤黑边区域的检测框
        detected_items = cls._filter_black_edge_detections(detected_items, img, img_width, img_height)
        # 重新统计模型检测的空货架（因为可能被过滤掉了）
        model_detected_empty_shelves = [item for item in detected_items 
                                       if any(keyword in item[0].lower() for keyword in empty_keywords)]

        # 3. 空货架推算算法（根据配置决定是否启用）
        # 只对非空货架的商品进行空位推算
        algo_empty_count = 0  # 记录算法推算的空货架数量
        
        if settings.enable_empty_detection and len(detected_items) >= 1:
            # 只使用商品（非空货架）来计算平均尺寸
            # 支持的空货架关键字：empty, 空, missing, vacant, gap, 缺货
            empty_keywords = ["empty", "空", "missing", "vacant", "gap", "缺货"]
            products_only = [item for item in detected_items 
                           if not any(keyword in item[0].lower() for keyword in empty_keywords)]
            
            if len(products_only) >= 1:
                print(f"\n算法推算空货架:")
                print(f"  - 用于推算的商品数: {len(products_only)}")
                
                # 计算平均尺寸（仅基于商品）
                avg_width = sum(item[3] - item[1] for item in products_only) / len(products_only)
                avg_height = sum(item[4] - item[2] for item in products_only) / len(products_only)
                
                print(f"  - 平均商品宽度: {avg_width:.1f}px")
                print(f"  - 平均商品高度: {avg_height:.1f}px")
                
                # 将商品聚类成行（仅商品）
                rows = cls._cluster_into_rows(products_only, avg_height)
                
                print(f"  - 检测到 {len(rows)} 行商品")
                
                # 在每一行中检测空位（算法推算的空货架不需要置信度）
                for row in rows:
                    if len(row) >= settings.min_products_per_row:
                        empty_shelves = cls._detect_gaps_in_row(row, avg_width, img_width, img)
                        detected_items.extend(empty_shelves)
                        algo_empty_count += len(empty_shelves)
                
                print(f"  - 算法推算的空货架: {algo_empty_count}")
                
                # 移除与商品重叠的空货架检测框（包括模型检测的和算法推算的）
                before_remove = len(detected_items)
                detected_items = cls._remove_overlapping_empty_shelves(detected_items)
                removed = before_remove - len(detected_items)
                if removed > 0:
                    print(f"  - 移除重叠的空货架: {removed}")
            else:
                print(f"\n⚠ 没有商品用于推算空货架")

        # 4. 计算统计信息（在移除重叠后重新统计）
        stats = cls._calculate_statistics(detected_items)
        
        # 重新统计模型检测的空货架数量（移除重叠后）
        empty_keywords = ["empty", "空", "missing", "vacant", "gap", "缺货"]
        final_model_empty_count = 0
        final_algo_empty_count = 0
        
        for item in detected_items:
            label, x1, y1, x2, y2, score = item
            is_empty = any(keyword in label.lower() for keyword in empty_keywords)
            if is_empty:
                if score >= 0:  # 模型检测的（有置信度）
                    final_model_empty_count += 1
                else:  # 算法推算的（置信度为-1）
                    final_algo_empty_count += 1
        
        print(f"\n最终统计:")
        print(f"  - 商品: {stats['product_count']}")
        print(f"  - 空货架总数: {stats['empty_count']}")
        print(f"    * 模型检测: {final_model_empty_count}")
        print(f"    * 算法推算: {final_algo_empty_count}")
        print(f"  - 总货位: {stats['total_slots']}")
        print(f"  - 缺货率: {stats['empty_rate']:.1%}")
        
        print(f"\n检测框类型:")
        print(f"  🟩 绿色实线: {stats['product_count']} 个（商品）")
        if final_model_empty_count > 0:
            print(f"  🟥 红色实线: {final_model_empty_count} 个（模型检测的空货架）")
        if final_algo_empty_count > 0:
            print(f"  🔵 蓝色虚线: {final_algo_empty_count} 个（算法推算的空货架）")
        print(f"{'='*70}\n")
        
        # 5. 绘制可视化结果
        overlay = img.copy()
        
        # 支持的空货架关键字
        empty_keywords = ["empty", "空", "missing", "vacant", "gap", "缺货"]
        
        # 绘制检测框
        for item in detected_items:
            label, x1, y1, x2, y2, score = item
            
            # 判断是否为空货架
            is_empty_shelf = any(keyword in label.lower() for keyword in empty_keywords)
            
            # 根据类型和来源设置样式
            if is_empty_shelf:
                if score < 0:
                    # 算法推算的空货架：蓝色虚线
                    color = (255, 0, 0)  # 蓝色 (BGR)
                    thickness = 1  # 细线
                    line_type = cv2.LINE_4  # 虚线效果
                else:
                    # 模型检测的空货架：红色实线
                    color = (0, 0, 255)  # 红色 (BGR)
                    thickness = 1  # 细线
                    line_type = cv2.LINE_AA  # 抗锯齿
            else:
                # 商品：绿色实线
                color = (0, 255, 0)  # 绿色 (BGR)
                thickness = 1  # 细线
                line_type = cv2.LINE_AA  # 抗锯齿
            
            # 绘制矩形框
            if is_empty_shelf and score < 0:
                # 算法推算的空货架绘制虚线效果
                x1_int, y1_int, x2_int, y2_int = int(x1), int(y1), int(x2), int(y2)
                # 绘制虚线矩形（通过绘制短线段实现）
                dash_length = 10
                gap_length = 5
                
                # 上边
                for i in range(x1_int, x2_int, dash_length + gap_length):
                    cv2.line(overlay, (i, y1_int), (min(i + dash_length, x2_int), y1_int), color, thickness)
                # 下边
                for i in range(x1_int, x2_int, dash_length + gap_length):
                    cv2.line(overlay, (i, y2_int), (min(i + dash_length, x2_int), y2_int), color, thickness)
                # 左边
                for i in range(y1_int, y2_int, dash_length + gap_length):
                    cv2.line(overlay, (x1_int, i), (x1_int, min(i + dash_length, y2_int)), color, thickness)
                # 右边
                for i in range(y1_int, y2_int, dash_length + gap_length):
                    cv2.line(overlay, (x2_int, i), (x2_int, min(i + dash_length, y2_int)), color, thickness)
            else:
                # 实线矩形
                cv2.rectangle(overlay, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness, line_type)
            
            # 绘制标签（只显示置信度）
            # 支持的空货架关键字：empty, 空, missing, vacant, gap, 缺货
            empty_keywords = ["empty", "空", "missing", "vacant", "gap", "缺货"]
            is_empty_shelf = any(keyword in label.lower() for keyword in empty_keywords)
            
            if is_empty_shelf and score < 0:
                # 算法推算的空货架：显示"算法"
                label_text = "算法"
            else:
                # 模型检测的结果：只显示置信度
                label_text = f"{score:.2f}"
            
            font_scale = 0.5
            font_thickness = 1
            
            # 计算文本大小
            (text_width, text_height), baseline = cv2.getTextSize(
                label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness
            )
            
            # 绘制文本背景
            cv2.rectangle(
                overlay,
                (int(x1), int(y1) - text_height - 10),
                (int(x1) + text_width, int(y1)),
                color,
                -1
            )
            
            # 绘制文本
            cv2.putText(
                overlay,
                label_text,
                (int(x1), int(y1) - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (255, 255, 255),
                font_thickness
            )

        # 添加统计信息到图片
        stats_text = [
            f"Products: {stats['product_count']}",
            f"Empty: {stats['empty_count']}",
            f"Total: {stats['total_slots']}",
            f"Empty Rate: {stats['empty_rate']:.1%}"
        ]
        
        y_offset = 30
        for text in stats_text:
            cv2.putText(
                overlay,
                text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )
            y_offset += 30

        # 混合原图与标注层，生成半透明效果
        vis_img = cv2.addWeighted(overlay, 0.6, img, 0.4, 0)
        
        # 保存结果
        img_name = os.path.basename(image_path)
        save_path = os.path.join(save_dir, "res_" + img_name)
        cv2.imwrite(save_path, vis_img)

        # 转换为元组列表
        final_boxes = [tuple(item) for item in detected_items]
        return save_path, final_boxes

    @classmethod
    def predict_on_video(cls, video_path: str, save_dir: str, conf_threshold: float = 0.25,
                         iou_threshold: float = 0.45, model_path: str = None) -> tuple[str, int, list]:
        """
        对视频进行检测，包括商品检测和空货架推算（已优化性能）
        
        Args:
            video_path: 视频路径
            save_dir: 保存目录
            conf_threshold: 置信度阈值
            iou_threshold: IOU 阈值
            model_path: 模型文件路径（可选，如果为 None 则使用默认模型）
            
        Returns:
            (保存的视频路径, 空货架最大值, 空货架最多的那一帧的检测框列表)
        """
        import time
        start_time = time.time()
        
        print(f"\n{'='*70}")
        print(f"视频检测 - {os.path.basename(video_path)}")
        print(f"{'='*70}")
        
        model = cls.load_model(model_path)
        
        # GPU 加速配置
        if settings.video_use_gpu:
            try:
                import torch
                if torch.cuda.is_available():
                    device = 'cuda'
                    print(f"✓ 使用 GPU 加速: {torch.cuda.get_device_name(0)}")
                else:
                    device = 'cpu'
                    print("⚠ GPU 不可用，使用 CPU")
            except ImportError:
                device = 'cpu'
                print("⚠ PyTorch 未安装，使用 CPU")
        else:
            device = 'cpu'
            print("使用 CPU 处理")
        
        os.makedirs(save_dir, exist_ok=True)

        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")

        # 获取视频属性
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"\n视频信息:")
        print(f"  - 分辨率: {width}×{height}")
        print(f"  - 帧率: {fps} fps")
        print(f"  - 总帧数: {total_frames}")
        print(f"  - 时长: {total_frames/fps:.1f} 秒")

        # 计算处理分辨率
        process_width = settings.video_process_width
        if width > process_width:
            scale = process_width / width
            process_height = int(height * scale)
            print(f"降低分辨率: {width}×{height} → {process_width}×{process_height} (缩放 {scale:.2f})")
        else:
            scale = 1.0
            process_width = width
            process_height = height
            print(f"保持原始分辨率: {width}×{height}")

        # 创建视频写入器
        video_name = os.path.basename(video_path)
        output_name = "res_" + os.path.splitext(video_name)[0] + ".mp4"
        output_path = os.path.join(save_dir, output_name)
        
        # 尝试使用 H264 编码器
        fourcc = None
        for codec in ['avc1', 'H264', 'mp4v', 'XVID']:
            try:
                fourcc = cv2.VideoWriter_fourcc(*codec)
                test_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
                if test_writer.isOpened():
                    test_writer.release()
                    print(f"使用编码器: {codec}")
                    break
                test_writer.release()
            except:
                continue
        
        if fourcc is None:
            raise ValueError("没有可用的视频编码器")
        
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            raise ValueError(f"无法创建视频写入器: {output_path}")

        frame_count = 0
        processed_count = 0
        max_empty_count = 0
        max_empty_frame_boxes = []
        last_detected_items = []
        
        skip_frames = settings.video_skip_frames
        direct_draw = settings.video_direct_draw
        
        print(f"\n性能优化配置:")
        print(f"  - 跳帧间隔: 每 {skip_frames} 帧检测一次")
        print(f"  - 处理分辨率: {process_width}×{process_height}")
        print(f"  - 直接绘制: {direct_draw}")
        print(f"  - GPU 加速: {device}")
        print(f"\n开始处理...\n")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                
                # 跳帧优化：只处理部分帧
                if frame_count % skip_frames != 0:
                    # 使用上一帧的检测结果绘制
                    if last_detected_items:
                        frame = cls._draw_detections_fast(
                            frame, last_detected_items, frame_count, total_frames, direct_draw
                        )
                    out.write(frame)
                    continue

                processed_count += 1
                
                # 降低分辨率优化
                if scale < 1.0:
                    small_frame = cv2.resize(frame, (process_width, process_height))
                else:
                    small_frame = frame

                # 执行检测
                results = model.predict(
                    source=small_frame,
                    conf=conf_threshold,
                    iou=iou_threshold,
                    save=False,
                    verbose=False,
                    device=device,
                    stream=False
                )

                if results:
                    r = results[0]
                    boxes_raw = r.boxes.xyxy.cpu().numpy()
                    scores_raw = r.boxes.conf.cpu().numpy()
                    classes_raw = r.boxes.cls.cpu().numpy()
                    names = model.names

                    # 整理检测到的商品和模型检测的空货架
                    detected_items = []
                    empty_keywords = ["empty", "空", "missing", "vacant", "gap", "缺货"]
                    
                    for b, s, c in zip(boxes_raw, scores_raw, classes_raw):
                        x1, y1, x2, y2 = map(float, b.tolist())
                        class_name = names[int(c)]
                        confidence = float(s)
                        
                        # 还原到原始分辨率
                        if scale < 1.0:
                            x1 /= scale
                            y1 /= scale
                            x2 /= scale
                            y2 /= scale
                        
                        detected_items.append([class_name, x1, y1, x2, y2, confidence])

                    # 过滤黑边区域的检测框
                    detected_items = cls._filter_black_edge_detections(detected_items, frame, width, height)

                    # 空货架推算（只对非空货架的商品进行空位推算）
                    if settings.enable_empty_detection and len(detected_items) >= 1:
                        # 只使用商品（非空货架）来计算平均尺寸
                        products_only = [item for item in detected_items 
                                       if not any(keyword in item[0].lower() for keyword in empty_keywords)]
                        
                        if len(products_only) >= 1:
                            avg_width = sum(item[3] - item[1] for item in products_only) / len(products_only)
                            avg_height = sum(item[4] - item[2] for item in products_only) / len(products_only)
                            
                            rows = cls._cluster_into_rows(products_only, avg_height)
                            
                            for row in rows:
                                if len(row) >= settings.min_products_per_row:
                                    empty_shelves = cls._detect_gaps_in_row(row, avg_width, width, small_frame)
                                    detected_items.extend(empty_shelves)
                            
                            detected_items = cls._remove_overlapping_empty_shelves(detected_items)
                    
                    # 统计空货架数量
                    current_empty_count = sum(1 for item in detected_items if item[0] == "empty_shelf")
                    
                    if current_empty_count > max_empty_count:
                        max_empty_count = current_empty_count
                        max_empty_frame_boxes = detected_items.copy()
                    
                    last_detected_items = detected_items

                    # 绘制检测结果
                    frame = cls._draw_detections_fast(
                        frame, detected_items, frame_count, total_frames, direct_draw
                    )

                out.write(frame)
                
                # 进度显示
                if processed_count % 10 == 0:
                    progress = frame_count / total_frames * 100
                    elapsed = time.time() - start_time
                    fps_current = frame_count / elapsed if elapsed > 0 else 0
                    eta = (total_frames - frame_count) / fps_current if fps_current > 0 else 0
                    print(f"进度: {progress:.1f}% ({frame_count}/{total_frames}), "
                          f"速度: {fps_current:.1f}fps, "
                          f"已用时: {elapsed:.1f}秒, "
                          f"预计剩余: {eta:.1f}秒")

        finally:
            cap.release()
            out.release()

        # 检查输出文件
        if not os.path.exists(output_path):
            raise ValueError(f"视频处理失败：输出文件未创建 {output_path}")

        total_time = time.time() - start_time
        print(f"\n{'='*70}")
        print(f"视频处理完成")
        print(f"{'='*70}")
        print(f"  - 总帧数: {total_frames}")
        print(f"  - 处理帧数: {processed_count}")
        print(f"  - 跳过帧数: {total_frames - processed_count}")
        print(f"  - 总用时: {total_time:.1f} 秒")
        print(f"  - 平均速度: {total_frames / total_time:.1f} fps")
        print(f"  - 空货架最大值: {max_empty_count}")
        print(f"  - 输出文件: {output_path}")
        print(f"{'='*70}\n")

        # FFmpeg 转码（可选）
        if settings.video_enable_ffmpeg:
            print("使用 FFmpeg 转码...")
            temp_path = None
            try:
                import subprocess
                import shutil
                
                temp_path = os.path.join(save_dir, f"temp_{int(os.path.getmtime(output_path))}.mp4")
                shutil.move(output_path, temp_path)
                
                subprocess.run([
                    'ffmpeg', '-i', temp_path,
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '23',
                    '-c:a', 'copy',
                    '-y',
                    output_path
                ], check=True, capture_output=True)
                
                os.remove(temp_path)
                temp_path = None
                print("✓ FFmpeg 转码完成")
            except FileNotFoundError:
                if temp_path and os.path.exists(temp_path):
                    shutil.move(temp_path, output_path)
                print("⚠ FFmpeg 未安装，跳过转码")
            except Exception as e:
                if temp_path and os.path.exists(temp_path):
                    shutil.move(temp_path, output_path)
                print(f"⚠ FFmpeg 转码失败: {e}")

        return output_path, max_empty_count, max_empty_frame_boxes
    
    @classmethod
    def _draw_detections_fast(cls, frame, detected_items, frame_count, total_frames, direct_draw=True):
        """快速绘制检测结果"""
        # 支持的空货架关键字
        empty_keywords = ["empty", "空", "missing", "vacant", "gap", "缺货"]
        
        if direct_draw:
            # 直接绘制（更快）
            for item in detected_items:
                label, x1, y1, x2, y2, score = item
                
                # 判断是否为空货架
                is_empty_shelf = any(keyword in label.lower() for keyword in empty_keywords)
                
                # 根据类型和来源设置样式
                if is_empty_shelf:
                    if score < 0:
                        # 算法推算的空货架：蓝色虚线
                        color = (255, 0, 0)  # 蓝色 (BGR)
                        thickness = 1
                        # 绘制虚线矩形
                        x1_int, y1_int, x2_int, y2_int = int(x1), int(y1), int(x2), int(y2)
                        dash_length = 8
                        gap_length = 4
                        
                        # 上边
                        for i in range(x1_int, x2_int, dash_length + gap_length):
                            cv2.line(frame, (i, y1_int), (min(i + dash_length, x2_int), y1_int), color, thickness)
                        # 下边
                        for i in range(x1_int, x2_int, dash_length + gap_length):
                            cv2.line(frame, (i, y2_int), (min(i + dash_length, x2_int), y2_int), color, thickness)
                        # 左边
                        for i in range(y1_int, y2_int, dash_length + gap_length):
                            cv2.line(frame, (x1_int, i), (x1_int, min(i + dash_length, y2_int)), color, thickness)
                        # 右边
                        for i in range(y1_int, y2_int, dash_length + gap_length):
                            cv2.line(frame, (x2_int, i), (x2_int, min(i + dash_length, y2_int)), color, thickness)
                    else:
                        # 模型检测的空货架：红色实线
                        color = (0, 0, 255)  # 红色 (BGR)
                        thickness = 1
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness, cv2.LINE_AA)
                else:
                    # 商品：绿色实线
                    color = (0, 255, 0)  # 绿色 (BGR)
                    thickness = 1
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness, cv2.LINE_AA)
                
                # 绘制标签（只显示置信度）
                if score < 0:
                    label_text = "算法"
                else:
                    label_text = f"{score:.2f}"
                
                cv2.putText(frame, label_text, (int(x1), int(y1) - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        else:
            # 半透明绘制（更美观但更慢）
            overlay = frame.copy()
            for item in detected_items:
                label, x1, y1, x2, y2, score = item
                
                # 判断是否为空货架
                is_empty_shelf = any(keyword in label.lower() for keyword in empty_keywords)
                
                # 根据类型和来源设置样式
                if is_empty_shelf:
                    if score < 0:
                        # 算法推算的空货架：蓝色虚线
                        color = (255, 0, 0)  # 蓝色 (BGR)
                        thickness = 1
                        # 绘制虚线矩形
                        x1_int, y1_int, x2_int, y2_int = int(x1), int(y1), int(x2), int(y2)
                        dash_length = 8
                        gap_length = 4
                        
                        for i in range(x1_int, x2_int, dash_length + gap_length):
                            cv2.line(overlay, (i, y1_int), (min(i + dash_length, x2_int), y1_int), color, thickness)
                        for i in range(x1_int, x2_int, dash_length + gap_length):
                            cv2.line(overlay, (i, y2_int), (min(i + dash_length, x2_int), y2_int), color, thickness)
                        for i in range(y1_int, y2_int, dash_length + gap_length):
                            cv2.line(overlay, (x1_int, i), (x1_int, min(i + dash_length, y2_int)), color, thickness)
                        for i in range(y1_int, y2_int, dash_length + gap_length):
                            cv2.line(overlay, (x2_int, i), (x2_int, min(i + dash_length, y2_int)), color, thickness)
                    else:
                        # 模型检测的空货架：红色实线
                        color = (0, 0, 255)  # 红色 (BGR)
                        thickness = 1
                        cv2.rectangle(overlay, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness, cv2.LINE_AA)
                else:
                    # 商品：绿色实线
                    color = (0, 255, 0)  # 绿色 (BGR)
                    thickness = 1
                    cv2.rectangle(overlay, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness, cv2.LINE_AA)
                
                # 绘制标签（只显示置信度）
                if score < 0:
                    label_text = "算法"
                else:
                    label_text = f"{score:.2f}"
                
                cv2.putText(overlay, label_text, (int(x1), int(y1) - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
        
        # 添加统计信息
        stats = cls._calculate_statistics(detected_items)
        stats_text = [
            f"Products: {stats['product_count']}",
            f"Empty: {stats['empty_count']}",
            f"Frame: {frame_count}/{total_frames}"
        ]
        
        y_offset = 30
        for text in stats_text:
            cv2.putText(frame, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            y_offset += 30
        
        return frame
