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

    @classmethod
    def load_model(cls):
        """加载YOLO模型（单例模式）"""
        if cls._model is None:
            cls._model = YOLO(settings.yolo_weights)
        return cls._model

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
    def _detect_gaps_in_row(cls, row: List[List], avg_width: float, img_width: int) -> List[List]:
        """
        检测一行中的空位
        
        Args:
            row: 该行的商品列表
            avg_width: 平均商品宽度
            img_width: 图片宽度
            
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
                # 创建空货架框
                empty_shelf = [
                    "empty_shelf",
                    gap_start,
                    row_y1,
                    gap_end,
                    row_y2,
                    0.99
                ]
                empty_shelves.append(empty_shelf)
        
        # 检测货架边缘的空位（可选）
        if settings.edge_detection and len(row_sorted) >= settings.min_products_per_row:
            # 左边缘空位
            left_edge_gap = row_sorted[0][1]  # 第一个商品的左边界
            if left_edge_gap > avg_width * settings.gap_threshold:
                empty_shelf = [
                    "empty_shelf",
                    0,
                    row_y1,
                    row_sorted[0][1],
                    row_y2,
                    0.95
                ]
                empty_shelves.append(empty_shelf)
            
            # 右边缘空位
            right_edge_gap = img_width - row_sorted[-1][3]  # 图片宽度 - 最后一个商品的右边界
            if right_edge_gap > avg_width * settings.gap_threshold:
                empty_shelf = [
                    "empty_shelf",
                    row_sorted[-1][3],
                    row_y1,
                    img_width,
                    row_y2,
                    0.95
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
                         iou_threshold: float = 0.45) -> Tuple[
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
            
        Returns:
            (保存路径, 检测结果列表)
        """
        model = cls.load_model()
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

        # 2. 整理检测到的商品
        detected_items = []
        for b, s, c in zip(boxes_raw, scores_raw, classes_raw):
            x1, y1, x2, y2 = map(float, b.tolist())
            detected_items.append([names[int(c)], x1, y1, x2, y2, float(s)])

        # 3. 空货架推算算法（优化版）
        if len(detected_items) >= 1:
            # 计算平均尺寸
            avg_width = sum(item[3] - item[1] for item in detected_items) / len(detected_items)
            avg_height = sum(item[4] - item[2] for item in detected_items) / len(detected_items)
            
            # 将商品聚类成行
            rows = cls._cluster_into_rows(detected_items, avg_height)
            
            # 在每一行中检测空位
            for row in rows:
                if len(row) >= settings.min_products_per_row:
                    empty_shelves = cls._detect_gaps_in_row(row, avg_width, img_width)
                    detected_items.extend(empty_shelves)

        # 4. 计算统计信息
        stats = cls._calculate_statistics(detected_items)
        
        # 5. 绘制可视化结果
        overlay = img.copy()
        
        # 绘制检测框
        for item in detected_items:
            label, x1, y1, x2, y2, score = item
            
            # 空货架用红色，商品用绿色
            if label == "empty_shelf":
                color = (0, 0, 255)  # 红色
                thickness = 3
            else:
                color = (0, 255, 0)  # 绿色
                thickness = 2
            
            # 绘制矩形框
            cv2.rectangle(overlay, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)
            
            # 绘制标签
            label_text = f"{label} {score:.2f}"
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
                         iou_threshold: float = 0.45) -> str:
        """
        对视频进行检测，包括商品检测和空货架推算
        
        Args:
            video_path: 视频路径
            save_dir: 保存目录
            conf_threshold: 置信度阈值
            iou_threshold: IOU 阈值
            
        Returns:
            保存的视频路径
        """
        model = cls.load_model()
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

        # 创建视频写入器（使用 H264 编码器以获得更好的浏览器兼容性）
        video_name = os.path.basename(video_path)
        output_name = "res_" + os.path.splitext(video_name)[0] + ".mp4"
        output_path = os.path.join(save_dir, output_name)
        
        # 尝试使用 H264 编码器，如果不可用则使用 mp4v
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
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                
                # 每隔几帧处理一次（提高速度）
                if frame_count % 2 != 0:  # 处理偶数帧
                    out.write(frame)
                    continue

                # 执行检测
                results = model.predict(
                    source=frame,
                    conf=conf_threshold,
                    iou=iou_threshold,
                    save=False,
                    verbose=False,
                    stream=False  # 逐帧处理，不需要 stream
                )

                if results:
                    r = results[0]
                    boxes_raw = r.boxes.xyxy.cpu().numpy()
                    scores_raw = r.boxes.conf.cpu().numpy()
                    classes_raw = r.boxes.cls.cpu().numpy()
                    names = model.names

                    # 整理检测到的商品
                    detected_items = []
                    for b, s, c in zip(boxes_raw, scores_raw, classes_raw):
                        x1, y1, x2, y2 = map(float, b.tolist())
                        detected_items.append([names[int(c)], x1, y1, x2, y2, float(s)])

                    # 空货架推算
                    if len(detected_items) >= 1:
                        avg_width = sum(item[3] - item[1] for item in detected_items) / len(detected_items)
                        avg_height = sum(item[4] - item[2] for item in detected_items) / len(detected_items)
                        
                        rows = cls._cluster_into_rows(detected_items, avg_height)
                        
                        for row in rows:
                            if len(row) >= settings.min_products_per_row:
                                empty_shelves = cls._detect_gaps_in_row(row, avg_width, width)
                                detected_items.extend(empty_shelves)

                    # 绘制检测结果
                    overlay = frame.copy()
                    for item in detected_items:
                        label, x1, y1, x2, y2, score = item
                        
                        if label == "empty_shelf":
                            color = (0, 0, 255)
                            thickness = 3
                        else:
                            color = (0, 255, 0)
                            thickness = 2
                        
                        cv2.rectangle(overlay, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)
                        
                        label_text = f"{label} {score:.2f}"
                        cv2.putText(
                            overlay,
                            label_text,
                            (int(x1), int(y1) - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (255, 255, 255),
                            1
                        )

                    # 添加统计信息
                    stats = cls._calculate_statistics(detected_items)
                    stats_text = [
                        f"Products: {stats['product_count']}",
                        f"Empty: {stats['empty_count']}",
                        f"Frame: {frame_count}/{total_frames}"
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

                    frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

                out.write(frame)

        finally:
            cap.release()
            out.release()

        # 检查输出文件是否成功创建
        if not os.path.exists(output_path):
            raise ValueError(f"视频处理失败：输出文件未创建 {output_path}")

        # 尝试使用 ffmpeg 重新编码以确保浏览器兼容性
        temp_path = None
        try:
            import subprocess
            import shutil
            
            # 创建临时文件名（避免中文字符问题）
            temp_path = os.path.join(save_dir, f"temp_{int(os.path.getmtime(output_path))}.mp4")
            shutil.move(output_path, temp_path)
            
            # 使用 ffmpeg 重新编码为 H264
            subprocess.run([
                'ffmpeg', '-i', temp_path,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'copy',
                '-y',
                output_path
            ], check=True, capture_output=True)
            
            # 删除临时文件
            os.remove(temp_path)
            temp_path = None
        except FileNotFoundError:
            # ffmpeg 未安装
            if temp_path and os.path.exists(temp_path):
                shutil.move(temp_path, output_path)
            print("FFmpeg 未安装，使用原始编码")
        except Exception as e:
            # 如果 ffmpeg 失败，恢复原始文件
            if temp_path and os.path.exists(temp_path):
                shutil.move(temp_path, output_path)
            print(f"FFmpeg 转码失败，使用原始编码: {e}")

        return output_path