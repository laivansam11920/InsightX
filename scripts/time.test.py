from time import time
import functools


def do_thoi_gian(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        bat_dau = time()
        ket_qua = func(*args, **kwargs)

        ket_thuc = time()
        print(f"Hàm '{func.__name__}' chạy mất: {ket_thuc - bat_dau:.4f} giây")
        return ket_qua

    return wrapper
