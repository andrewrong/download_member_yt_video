import os
import logging
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv
import yt_dlp
import browser_cookie3
from browser_cookie3 import BrowserCookieError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 配置常量
DEFAULT_COOKIES_FILE = 'youtube_cookies.txt'
DEFAULT_URLS_FILE = 'urls.txt'
DEFAULT_OUTPUT_TEMPLATE = '%(title)s.%(ext)s'


class Config:
    """配置管理类"""
    def __init__(self, audio_only=False, audio_quality=2):
        self.profile_path = self._get_profile_path()
        self.cookies_file = DEFAULT_COOKIES_FILE
        self.urls_file = DEFAULT_URLS_FILE
        self.output_template = DEFAULT_OUTPUT_TEMPLATE
        self.download_dir = self._get_download_dir()
        self.audio_only = audio_only
        self.audio_quality = audio_quality
        self.proxy = os.getenv('PROXY')

        # 过滤空值
        if self.proxy and self.proxy.strip():
            self.proxy = self.proxy.strip()
            logger.info(f"使用代理: {self.proxy}")
        else:
            self.proxy = None

        # 显示音频设置
        logger.info(f"音频仅下载模式: {'启用' if self.audio_only else '禁用'}")
        quality_names = {0: '最差', 1: '较差', 2: '良好', 3: '很好', 4: '极好', 5: '最佳'}
        logger.info(f"音频质量设置: {self.audio_quality} ({quality_names.get(self.audio_quality, '未知')})")

    def _get_profile_path(self) -> str:
        """获取 Chrome 配置文件路径"""
        profile_path = os.getenv('PROFILE_PATH')
        if not profile_path:
            raise ValueError("请在 .env 文件中设置 PROFILE_PATH 变量")

        if not os.path.exists(profile_path):
            raise FileNotFoundError(f"Chrome 配置文件不存在: {profile_path}")

        logger.info(f"使用 Chrome 配置文件: {profile_path}")
        return profile_path

    def _get_download_dir(self) -> str:
        """获取下载目录路径"""
        download_dir = os.getenv('DOWNLOAD_DIR')

        # 设置默认下载目录
        if not download_dir:
            download_dir = "/Volumes/nomoshen_macmini/data/data_backup/youtube"

        # 确保目录存在
        os.makedirs(download_dir, exist_ok=True)

        logger.info(f"使用下载目录: {download_dir}")
        return download_dir

    

class YouTubeDownloader:
    """YouTube 视频下载器主类"""
    def __init__(self, audio_only=False, audio_quality=2):
        self.config = Config(audio_only=audio_only, audio_quality=audio_quality)

    def get_cookies(self) -> bool:
        """获取并保存 cookies"""
        try:
            logger.info("正在获取 cookies...")
            cj = browser_cookie3.chrome(
                cookie_file=self.config.profile_path,
                domain_name='youtube.com'
            )
            logger.info(f"成功获取 {len(cj)} 个 cookies")

            # 过滤出重要的 YouTube cookies
            youtube_cookies = []
            essential_cookies = ['__Secure-3PSID', '__Secure-3PAPISID', 'SAPISID', 'HSID', 'SSID', 'APISID', 'SID']
            required_cookies = ['SAPISID', '__Secure-3PSID']

            for cookie in cj:
                if any(essential in cookie.name for essential in essential_cookies):
                    youtube_cookies.append({
                        'name': cookie.name,
                        'value': cookie.value,
                        'domain': cookie.domain,
                        'path': cookie.path,
                        'expires': cookie.expires,
                        'secure': cookie.secure,
                    })

            # 检查必需的 cookies
            found_required = []
            for req_cookie in required_cookies:
                if any(req_cookie in cookie['name'] for cookie in youtube_cookies):
                    found_required.append(req_cookie)

            if not youtube_cookies:
                logger.error("未找到任何 YouTube cookies")
                return False

            if len(found_required) < 2:
                logger.error(f"缺少必需的 cookies，只找到: {found_required}")
                return False

            logger.info(f"找到 {len(youtube_cookies)} 个 YouTube cookies")
            logger.info(f"必需 cookies: {found_required}")

            # 保存 cookies 到文件
            with open(self.config.cookies_file, 'w', encoding='utf-8') as f:
                f.write("# Netscape HTTP Cookie File\n")
                youtube_domain_cookies = [c for c in youtube_cookies if c['domain'] == '.youtube.com']

                for cookie in youtube_domain_cookies:
                    secure = "TRUE" if cookie['secure'] else "FALSE"
                    expires = int(cookie['expires']) if cookie['expires'] else 0
                    f.write(f"{cookie['domain']}\tTRUE\t{cookie['path']}\t{secure}\t{expires}\t{cookie['name']}\t{cookie['value']}\n")

            logger.info(f"成功保存 {len(youtube_domain_cookies)} 个 YouTube cookies")
            return True

        except BrowserCookieError as e:
            logger.error(f"获取 cookies 失败: {e}")
            return False
        except Exception as e:
            logger.error(f"获取 cookies 时发生错误: {e}")
            return False

    def _get_channel_name(self, url: str) -> str:
        """获取视频频道名称"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'cookiefile': self.config.cookies_file,
            }

            if self.config.proxy:
                ydl_opts['proxy'] = self.config.proxy

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # 尝试获取频道名称
                channel_name = None

                # 优先从uploader字段获取
                if info.get('uploader'):
                    channel_name = info['uploader']
                # 其次从channel字段获取
                elif info.get('channel'):
                    channel_name = info['channel']
                # 最后从channel_id获取
                elif info.get('channel_id'):
                    channel_name = info['channel_id']

                # 清理频道名称，移除特殊字符
                if channel_name:
                    # 移除不允许的文件名字符
                    channel_name = ''.join(c for c in channel_name if c.isalnum() or c in (' ', '-', '_', '.', '(', ')'))
                    channel_name = channel_name.strip()
                    if not channel_name:
                        channel_name = "UnknownChannel"
                else:
                    channel_name = "UnknownChannel"

                logger.info(f"获取到频道名称: {channel_name}")
                return channel_name

        except Exception as e:
            logger.warning(f"获取频道名称失败: {e}，使用默认名称")
            return "UnknownChannel"

    def download_video(self, url: str) -> bool:
        """下载单个视频或音频"""
        try:
            # 获取频道名称
            channel_name = self._get_channel_name(url)

            # 创建频道目录
            channel_dir = os.path.join(self.config.download_dir, channel_name)
            os.makedirs(channel_dir, exist_ok=True)

            # yt-dlp 配置
            ydl_opts = {
                'cookiefile': self.config.cookies_file,
                'outtmpl': os.path.join(channel_dir, self.config.output_template)
            }

            if self.config.proxy:
                ydl_opts['proxy'] = self.config.proxy

            # 音频下载设置
            if self.config.audio_only:
                ydl_opts.update({
                    'format': f'bestaudio[acodec^=opus]/bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': str(self.config.audio_quality),
                    }],
                    'writethumbnail': False,
                    'keepvideo': False
                })
                download_type = "音频"
                file_extension = "mp3"
            else:
                ydl_opts.update({
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                })
                download_type = "视频"
                file_extension = "mp4"

            logger.info(f"开始下载{download_type}: {url} 到频道目录: {channel_name}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logger.info(f"下载完成: {url}")
            return True

        except Exception as e:
            logger.error(f"下载失败: {url}, 错误: {e}")
            return False

    def download_urls(self, urls: List[str]) -> Dict[str, int]:
        """批量下载视频"""
        results = {
            'total': len(urls),
            'success': 0,
            'failed': 0,
            'unavailable': 0
        }

        logger.info(f"开始批量下载 {len(urls)} 个视频")

        # 获取 cookies
        if not self.get_cookies():
            logger.error("无法获取有效的 cookies，程序终止")
            return results

        logger.info("Cookies 准备就绪，开始下载视频...")

        for i, url in enumerate(urls, 1):
            logger.info(f"处理第 {i}/{len(urls)} 个视频: {url}")

            # # 检查视频可用性
            # if not self._check_video_available(url):
            #     logger.warning(f"跳过 {url} - 视频不可用")
            #     results['unavailable'] += 1
            #     continue

            # 下载视频
            if self.download_video(url):
                results['success'] += 1
            else:
                results['failed'] += 1

        logger.info(f"批量下载完成: 成功 {results['success']}, 失败 {results['failed']}, 不可用 {results['unavailable']}")
        return results

    def list_formats(self, url: str) -> bool:
        """列出视频所有可用格式"""
        try:
            # 获取频道名称用于显示
            channel_name = self._get_channel_name(url)
            channel_dir = os.path.join(self.config.download_dir, channel_name)
            os.makedirs(channel_dir, exist_ok=True)

            ydl_opts = {
                'quiet': False,
                'no_warnings': False,
                'listformats': True,
                'cookiefile': self.config.cookies_file,
                'paths': {'home': channel_dir}
            }

            if self.config.proxy:
                ydl_opts['proxy'] = self.config.proxy

            # 如果是音频模式，只显示音频格式
            if self.config.audio_only:
                logger.info(f"正在获取音频格式信息: {url} (频道: {channel_name})")
                ydl_opts['format'] = 'bestaudio[acodec^=opus]/bestaudio/best'
            else:
                logger.info(f"正在获取视频格式信息: {url} (频道: {channel_name})")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=False)

            return True

        except Exception as e:
            logger.error(f"获取视频格式失败: {e}")
            return False

    def _check_video_available(self, url: str) -> bool:
        """检查视频是否可用"""
        try:
            channel_name = self._get_channel_name(url)
            channel_dir = os.path.join(self.config.download_dir, channel_name)
            os.makedirs(channel_dir, exist_ok=True)

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'cookiefile': self.config.cookies_file,
                'paths': {'home': channel_dir}
            }

            if self.config.proxy:
                ydl_opts['proxy'] = self.config.proxy

            # 根据模式检查不同类型的格式
            if self.config.audio_only:
                ydl_opts['format'] = 'bestaudio[acodec^=opus]/bestaudio/best'
                content_type = "音频"
            else:
                ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                content_type = "视频"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # 检查是否有可用的格式
                formats = info.get('formats', [])
                if self.config.audio_only:
                    # 检查音频格式
                    audio_formats = [f for f in formats if f.get('acodec') != 'none']
                    if not audio_formats:
                        logger.info(f"{content_type} '{info.get('title', 'Unknown')}' 没有可用的音频格式")
                        return False
                    logger.info(f"{content_type} '{info.get('title', 'Unknown')}' 可用，找到 {len(audio_formats)} 个音频格式")
                else:
                    # 检查视频格式
                    video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                    if not video_formats:
                        logger.info(f"{content_type} '{info.get('title', 'Unknown')}' 没有可用的视频格式")
                        return False
                    logger.info(f"{content_type} '{info.get('title', 'Unknown')}' 可用，找到 {len(video_formats)} 个视频格式")

                return True

        except Exception as e:
            logger.warning(f"检查视频可用性时出错: {e}")
            return False


def read_urls_from_file(file_path: str) -> List[str]:
    """从文件读取 URL 列表"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            urls = [line.strip() for line in file if line.strip()]

        # 验证 URL 格式
        valid_urls = []
        for url in urls:
            if url.startswith(('https://www.youtube.com/', 'https://youtube.com/')):
                valid_urls.append(url)
            else:
                logger.warning(f"跳过无效的 YouTube URL: {url}")

        logger.info(f"从 {file_path} 读取到 {len(valid_urls)} 个有效 URL")
        return valid_urls

    except FileNotFoundError:
        logger.error(f"URL 文件不存在: {file_path}")
        return []
    except Exception as e:
        logger.error(f"读取 URL 文件失败: {e}")
        return []


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='YouTube 视频下载器')
    parser.add_argument('--list-formats', '-l', action='store_true',
                       help='列出视频的可用格式而不下载')
    parser.add_argument('--url', '-u', type=str,
                       help='指定要处理的单个视频 URL')
    parser.add_argument('--audio-only', '-a', action='store_true',
                       help='仅下载音频（MP3格式）')
    parser.add_argument('--audio-quality', '-q', type=int, choices=range(0, 6), default=2,
                       help='音频质量：0（最差）到 5（最佳），默认为2（良好）')
    return parser.parse_args()

def main():
    """主函数"""
    try:
        args = parse_args()

        # 创建下载器实例，传入命令行参数
        downloader = YouTubeDownloader(
            audio_only=args.audio_only,
            audio_quality=args.audio_quality
        )

        if args.url:
            # 处理单个 URL
            url = args.url.strip()

            if args.list_formats:
                # 列出格式
                logger.info("正在获取格式信息...")
                if not downloader.get_cookies():
                    logger.error("无法获取有效的 cookies")
                    return

                downloader.list_formats(url)
            else:
                # 下载单个视频/音频
                content_type = "音频" if args.audio_only else "视频"
                logger.info(f"正在下载单个{content_type}...")
                if not downloader.get_cookies():
                    logger.error("无法获取有效的 cookies")
                    return

                success = downloader.download_video(url)
                print(f"\n下载结果: {'成功' if success else '失败'}")
        else:
            # 批量下载模式
            urls_file = downloader.config.urls_file
            if not os.path.exists(urls_file):
                logger.error(f"URL 文件不存在: {urls_file}")
                logger.info(f"请创建 {urls_file} 文件并添加要下载的 YouTube 视频链接")
                return

            urls = read_urls_from_file(urls_file)
            if not urls:
                logger.error("未找到有效的 YouTube URL")
                return

            if args.list_formats:
                # 列出所有视频的格式
                logger.info("正在获取所有视频的格式信息...")
                if not downloader.get_cookies():
                    logger.error("无法获取有效的 cookies")
                    return

                for url in urls:
                    print(f"\n{'='*50}")
                    downloader.list_formats(url)
            else:
                # 批量下载
                content_type = "音频" if args.audio_only else "视频"
                logger.info(f"开始批量下载{content_type}...")
                results = downloader.download_urls(urls)

                # 输出结果统计
                print(f"\n{content_type}下载完成统计:")
                print(f"总计: {results['total']} 个{content_type}")
                print(f"成功: {results['success']} 个")
                print(f"失败: {results['failed']} 个")
                print(f"不可用: {results['unavailable']} 个")

    except KeyboardInterrupt:
        logger.info("用户中断下载")
        print("\n下载已中断")
    except Exception as e:
        logger.error(f"程序执行错误: {e}")
        print(f"程序执行出错: {e}")


if __name__ == "__main__":
    main()
