import urllib.request
import sys
import traceback

def main():
    url = "http://127.0.0.1:8000/study/generate-plan/f47ac10b-58cc-4372-a567-0e02b2c3d479"
    req = urllib.request.Request(url, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("STATUS", r.status)
            body = r.read().decode()
            print(body)
    except Exception:
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
