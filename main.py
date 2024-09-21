import browser_cookie3
import json
import yt_dlp

def get_youtube_cookies():
    # macos 的配置，看你登录的浏览器，然后配置
    profile_path = '/Users/xxxxx/Library/Application Support/Google/Chrome/Profile 2/Cookies'
    # 获取 YouTube 的 cookies
    cj = browser_cookie3.chrome(cookie_file=profile_path,domain_name='youtube.com')
    
    print(f"cj: {cj}")
    # 将 cookies 转换为字典列表
    cookies_list = [
        {
            'name': cookie.name,
            'value': cookie.value,
            'domain': cookie.domain,
            'path': cookie.path,
            'expires': cookie.expires,
            'secure': cookie.secure
        }
        for cookie in cj
    ]
    
    return cookies_list

def save_cookies_to_file(cookies, filename='youtube_cookies.txt'):
    with open(filename, 'w') as f:
        f.write("# Netscape HTTP Cookie File\n")
        for cookie in cookies:
            if cookie['domain'] != '.youtube.com':
                continue
            secure = "TRUE" if cookie['secure'] else "FALSE"
            expires = int(cookie['expires']) if cookie['expires'] else 0
            f.write(f"{cookie['domain']}\tTRUE\t{cookie['path']}\t{secure}\t{expires}\t{cookie['name']}\t{cookie['value']}\n")

def download_video_with_cookies(url, cookies_filename='youtube_cookies.txt'):
    ydl_opts = {
        'cookiefile': cookies_filename,
        'outtmpl': '%(title)s.%(ext)s'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        print(f"下载完成：{url}")
    

def read_urls_from_file(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

# 使用示例

def main():
    urls = read_urls_from_file('urls.txt')
    for url in urls:
        # 获取并保存 cookies
        print(f"获取并保存 cookies: {url}")
        cookies = get_youtube_cookies()
        save_cookies_to_file(cookies)
        
        # 下载视频
        print(f"下载视频：{url}")
        download_video_with_cookies(url)

if __name__ == "__main__":
    main()