"""
压力测试服务

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-14
"""

import threading
import time
import uuid
import psutil
from datetime import datetime
from typing import Dict, Optional, List


class StressTestService:
    """
    压力测试服务
    
    负责执行 CPU 和内存压力测试，用于演示 HPA 自动扩展功能
    """
    
    def __init__(self):
        """初始化压力测试服务"""
        # 存储活动的压力测试
        self._active_tests: Dict[str, Dict] = {}
        
        # 线程锁，确保线程安全
        self._lock = threading.Lock()
        
        # 存储测试历史
        self._test_history: List[Dict] = []
        self._max_history = 100
    
    def start_cpu_stress(self, duration: int = 60, intensity: int = 80) -> str:
        """
        启动 CPU 压力测试
        
        Args:
            duration: 测试持续时间（秒），默认 60 秒
            intensity: 压力强度（1-100），默认 80
        
        Returns:
            测试 ID
        """
        # 生成唯一的测试 ID
        test_id = str(uuid.uuid4())
        
        # 限制参数范围
        duration = max(1, min(300, duration))  # 1-300 秒
        intensity = max(1, min(100, intensity))  # 1-100
        
        # 创建测试记录
        test_info = {
            'test_id': test_id,
            'test_type': 'cpu',
            'status': 'running',
            'start_time': datetime.utcnow().isoformat() + 'Z',
            'end_time': None,
            'duration': duration,
            'intensity': intensity,
            'initial_cpu': self.get_current_cpu_usage(),
            'peak_cpu': 0,
            'error': None
        }
        
        with self._lock:
            self._active_tests[test_id] = test_info
        
        # 在后台线程中执行压力测试
        thread = threading.Thread(
            target=self._run_cpu_stress,
            args=(test_id, duration, intensity),
            daemon=True
        )
        thread.start()
        
        return test_id
    
    def start_memory_stress(self, duration: int = 60, target_mb: int = 100) -> str:
        """
        启动内存压力测试
        
        Args:
            duration: 测试持续时间（秒），默认 60 秒
            target_mb: 目标内存分配大小（MB），默认 100 MB
        
        Returns:
            测试 ID
        """
        # 生成唯一的测试 ID
        test_id = str(uuid.uuid4())
        
        # 限制参数范围
        duration = max(1, min(300, duration))  # 1-300 秒
        target_mb = max(10, min(500, target_mb))  # 10-500 MB
        
        # 创建测试记录
        test_info = {
            'test_id': test_id,
            'test_type': 'memory',
            'status': 'running',
            'start_time': datetime.utcnow().isoformat() + 'Z',
            'end_time': None,
            'duration': duration,
            'target_mb': target_mb,
            'initial_memory': self.get_current_memory_usage(),
            'peak_memory': 0,
            'error': None
        }
        
        with self._lock:
            self._active_tests[test_id] = test_info
        
        # 在后台线程中执行压力测试
        thread = threading.Thread(
            target=self._run_memory_stress,
            args=(test_id, duration, target_mb),
            daemon=True
        )
        thread.start()
        
        return test_id
    
    def get_stress_status(self, test_id: str) -> Optional[Dict]:
        """
        获取压力测试状态
        
        Args:
            test_id: 测试 ID
        
        Returns:
            测试状态信息，如果测试不存在则返回 None
        """
        with self._lock:
            if test_id in self._active_tests:
                return self._active_tests[test_id].copy()
            
            # 检查历史记录
            for test in self._test_history:
                if test['test_id'] == test_id:
                    return test.copy()
        
        return None
    
    def stop_stress(self, test_id: str) -> bool:
        """
        停止压力测试
        
        Args:
            test_id: 测试 ID
        
        Returns:
            是否成功停止
        """
        with self._lock:
            if test_id in self._active_tests:
                test_info = self._active_tests[test_id]
                test_info['status'] = 'stopped'
                test_info['end_time'] = datetime.utcnow().isoformat() + 'Z'
                return True
        
        return False
    
    def get_current_cpu_usage(self) -> float:
        """
        获取当前 CPU 使用率
        
        Returns:
            CPU 使用率百分比（0-100）
        """
        try:
            # 获取 1 秒内的平均 CPU 使用率
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            print(f"获取 CPU 使用率失败: {e}")
            return 0.0
    
    def get_current_memory_usage(self) -> Dict:
        """
        获取当前内存使用情况
        
        Returns:
            内存使用信息字典
        """
        try:
            memory = psutil.virtual_memory()
            return {
                'total_mb': round(memory.total / (1024 * 1024), 2),
                'used_mb': round(memory.used / (1024 * 1024), 2),
                'available_mb': round(memory.available / (1024 * 1024), 2),
                'percent': memory.percent
            }
        except Exception as e:
            print(f"获取内存使用情况失败: {e}")
            return {
                'total_mb': 0,
                'used_mb': 0,
                'available_mb': 0,
                'percent': 0
            }
    
    def get_active_tests(self) -> List[Dict]:
        """
        获取所有活动的压力测试
        
        Returns:
            活动测试列表
        """
        with self._lock:
            return [test.copy() for test in self._active_tests.values()]
    
    def get_test_history(self, limit: int = 10) -> List[Dict]:
        """
        获取测试历史
        
        Args:
            limit: 返回的最大记录数
        
        Returns:
            测试历史列表
        """
        with self._lock:
            return self._test_history[-limit:][::-1]  # 返回最近的记录，倒序
    
    def get_all_active_tests(self) -> List[Dict]:
        """
        获取所有活动测试（包括活动测试和最近的历史记录）
        
        Returns:
            所有测试列表
        """
        with self._lock:
            # 合并活动测试和最近的历史记录
            all_tests = list(self._active_tests.values())
            # 添加最近的历史记录（最多 10 条）
            all_tests.extend(self._test_history[-10:])
            return all_tests
    
    def cleanup_completed_tests(self, max_age_seconds: int = 3600) -> int:
        """
        清理已完成的测试记录
        
        Args:
            max_age_seconds: 最大保留时间（秒）
        
        Returns:
            清理的记录数
        """
        with self._lock:
            cutoff_time = datetime.utcnow().timestamp() - max_age_seconds
            
            # 过滤历史记录
            original_count = len(self._test_history)
            self._test_history = [
                test for test in self._test_history
                if self._parse_test_timestamp(test.get('end_time', '')).timestamp() >= cutoff_time
            ]
            
            cleaned_count = original_count - len(self._test_history)
            return cleaned_count
    
    def _parse_test_timestamp(self, timestamp_str: str) -> datetime:
        """
        解析测试时间戳字符串
        
        Args:
            timestamp_str: ISO 格式的时间戳字符串
        
        Returns:
            datetime 对象
        """
        try:
            # 移除 'Z' 后缀
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, AttributeError):
            # 如果解析失败，返回很久以前的时间
            return datetime.min
    
    def _run_cpu_stress(self, test_id: str, duration: int, intensity: int) -> None:
        """
        执行 CPU 压力测试（内部方法）
        
        Args:
            test_id: 测试 ID
            duration: 持续时间（秒）
            intensity: 强度（1-100）
        """
        start_time = time.time()
        end_time = start_time + duration
        
        try:
            # 计算工作和休息的比例
            work_ratio = intensity / 100.0
            cycle_duration = 0.1  # 每个周期 0.1 秒
            work_time = cycle_duration * work_ratio
            rest_time = cycle_duration * (1 - work_ratio)
            
            while time.time() < end_time:
                # 检查是否被停止
                with self._lock:
                    if test_id not in self._active_tests:
                        break
                    if self._active_tests[test_id]['status'] == 'stopped':
                        break
                
                # 执行 CPU 密集型计算
                work_start = time.time()
                while time.time() - work_start < work_time:
                    # 执行一些计算密集型操作
                    _ = sum(i * i for i in range(1000))
                
                # 休息
                if rest_time > 0:
                    time.sleep(rest_time)
                
                # 更新峰值 CPU
                current_cpu = self.get_current_cpu_usage()
                with self._lock:
                    if test_id in self._active_tests:
                        if current_cpu > self._active_tests[test_id]['peak_cpu']:
                            self._active_tests[test_id]['peak_cpu'] = current_cpu
            
            # 测试完成
            with self._lock:
                if test_id in self._active_tests:
                    test_info = self._active_tests[test_id]
                    test_info['status'] = 'completed'
                    test_info['end_time'] = datetime.utcnow().isoformat() + 'Z'
                    test_info['final_cpu'] = self.get_current_cpu_usage()
                    
                    # 移动到历史记录
                    self._test_history.append(test_info)
                    if len(self._test_history) > self._max_history:
                        self._test_history = self._test_history[-self._max_history:]
                    
                    del self._active_tests[test_id]
        
        except Exception as e:
            # 记录错误
            with self._lock:
                if test_id in self._active_tests:
                    test_info = self._active_tests[test_id]
                    test_info['status'] = 'failed'
                    test_info['end_time'] = datetime.utcnow().isoformat() + 'Z'
                    test_info['error'] = str(e)
                    
                    # 移动到历史记录
                    self._test_history.append(test_info)
                    if len(self._test_history) > self._max_history:
                        self._test_history = self._test_history[-self._max_history:]
                    
                    del self._active_tests[test_id]
    
    def _run_memory_stress(self, test_id: str, duration: int, target_mb: int) -> None:
        """
        执行内存压力测试（内部方法）
        
        Args:
            test_id: 测试 ID
            duration: 持续时间（秒）
            target_mb: 目标内存大小（MB）
        """
        start_time = time.time()
        end_time = start_time + duration
        
        # 存储分配的内存
        memory_blocks = []
        
        try:
            # 分配内存（每个块 1 MB）
            block_size = 1024 * 1024  # 1 MB
            for _ in range(target_mb):
                # 检查是否被停止
                with self._lock:
                    if test_id not in self._active_tests:
                        break
                    if self._active_tests[test_id]['status'] == 'stopped':
                        break
                
                # 分配内存块
                memory_blocks.append(bytearray(block_size))
                
                # 更新峰值内存
                current_memory = self.get_current_memory_usage()
                with self._lock:
                    if test_id in self._active_tests:
                        if current_memory['used_mb'] > self._active_tests[test_id]['peak_memory']:
                            self._active_tests[test_id]['peak_memory'] = current_memory['used_mb']
                
                # 短暂休息，避免过快分配
                time.sleep(0.01)
            
            # 保持内存占用直到测试结束
            while time.time() < end_time:
                # 检查是否被停止
                with self._lock:
                    if test_id not in self._active_tests:
                        break
                    if self._active_tests[test_id]['status'] == 'stopped':
                        break
                
                # 定期访问内存，防止被优化掉
                if memory_blocks:
                    memory_blocks[0][0] = 1
                
                # 更新峰值内存
                current_memory = self.get_current_memory_usage()
                with self._lock:
                    if test_id in self._active_tests:
                        if current_memory['used_mb'] > self._active_tests[test_id]['peak_memory']:
                            self._active_tests[test_id]['peak_memory'] = current_memory['used_mb']
                
                time.sleep(1)
            
            # 测试完成
            with self._lock:
                if test_id in self._active_tests:
                    test_info = self._active_tests[test_id]
                    test_info['status'] = 'completed'
                    test_info['end_time'] = datetime.utcnow().isoformat() + 'Z'
                    test_info['final_memory'] = self.get_current_memory_usage()
                    
                    # 移动到历史记录
                    self._test_history.append(test_info)
                    if len(self._test_history) > self._max_history:
                        self._test_history = self._test_history[-self._max_history:]
                    
                    del self._active_tests[test_id]
        
        except Exception as e:
            # 记录错误
            with self._lock:
                if test_id in self._active_tests:
                    test_info = self._active_tests[test_id]
                    test_info['status'] = 'failed'
                    test_info['end_time'] = datetime.utcnow().isoformat() + 'Z'
                    test_info['error'] = str(e)
                    
                    # 移动到历史记录
                    self._test_history.append(test_info)
                    if len(self._test_history) > self._max_history:
                        self._test_history = self._test_history[-self._max_history:]
                    
                    del self._active_tests[test_id]
        
        finally:
            # 清理内存
            memory_blocks.clear()
