from concurrent.futures import ThreadPoolExecutor
from requests import get, head
import time

class Downloader:
    def __init__(self, url, num_threads, save_name):
        self.url = url
        self.num_threads = num_threads
        self.save_name = save_name
        self.total_size = 0
        
        r = head(self.url, allow_redirects=True)
        self.total_size = int(r.headers['Content-Length'])

    def download_chunk(self, start, end, chunk_size=10240):
        headers = {'Range': f'bytes={start}-{end}'}
        r = get(self.url, headers=headers, stream=True)
        
        with open(self.save_name, 'rb+') as f:
            f.seek(start)
            for chunk in r.iter_content(chunk_size):
                f.write(chunk)

    def __call__(self):
        with open(self.save_name, 'wb') as f:
            f.truncate(self.total_size)
        
        tp = ThreadPoolExecutor(max_workers=self.num_threads)
        futures = []
        start = 0
        chunk_size = self.total_size // self.num_threads
        for i in range(self.num_threads):
            start = i * chunk_size
            end = start + chunk_size - 1
            if i == self.num_threads - 1:
                end = self.total_size - 1
            future = tp.submit(self.download_chunk, start, end)
            futures.append(future)
        
        tp.shutdown()

