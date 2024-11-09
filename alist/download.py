from concurrent.futures import ThreadPoolExecutor
from requests import get, head
import time


class downloader:
    def __init__(self, url, num, name):
        self.url = url  # url
        self.num = num  # 线程数量
        self.name = name  # 保存名称
        self.getsize = 0  # 文件大小

        r = head(self.url, allow_redirects=True)
        self.size = int(r.headers["Content-Length"])

    def down(self, start, end, chunk_size=10240):

        headers = {"range": f"bytes={start}-{end}"}  # 头部
        r = get(self.url, headers=headers, stream=True)

        with open(self.name, "rb+") as f:
            f.seek(start)
            for chunk in r.iter_content(chunk_size):
                actual_chunk_size = len(chunk)
                f.write(chunk)
                self.getsize += actual_chunk_size

    def main(self):
        start_time = time.time()
        f = open(self.name, "wb")
        f.truncate(self.size)
        f.close()
        tp = ThreadPoolExecutor(max_workers=self.num)
        futures = []
        start = 0
        chunk_size = self.size // self.num
        for i in range(self.num):
            start = i * chunk_size
            end = start + chunk_size - 1
            if i == self.num - 1:
                end = self.size - 1  # 调整最后一个片段以确保覆盖剩余的字节
            future = tp.submit(self.down, start, end)
            futures.append(future)

        last_time = time.time()
        last_getsize = 0
        while True:
            current_time = time.time()
            current_getsize = self.getsize
            time_elapsed = current_time - start_time
            if current_getsize > self.size:
                current_getsize = self.size
            process = current_getsize / self.size * 100
            speed = (current_getsize - last_getsize) / (current_time - last_time)
            last_getsize = current_getsize
            last_time = current_time

            if speed >= 1024:
                speed_str = f"{speed / 1024/1024:.2f}MB/s"
            else:
                speed_str = f"{speed / 1024:.2f}KB/s"

            print(f"process: {process:.2f}% | speed: {speed_str}", end="\r")

            if process >= 99.9:
                print(f"process: 100.00% | speed: 00.00KB/s", end=" | ")
                break

            time.sleep(0.25)  # Adjust the interval for smoother progress updates

        tp.shutdown()
        end_time = time.time()
        total_time = end_time - start_time
        average_speed = self.size / total_time / 1024 / 1024
        print(f"total-time: {total_time:.0f}s | average-speed: {average_speed:.2f}MB/s")


if __name__ == "__main__":
    url = "https://autopatchcn.juequling.com/package_download/op/client_app/download/20240623113017_aqRjyJNQjPi1XNZN/mktbackup2/ZenlessZoneZero_1.0.apk"
    down = downloader(url, 12, "test.mp4")
    down.main()
