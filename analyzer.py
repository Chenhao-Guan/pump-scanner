from googleapiclient.discovery import build
import tweepy
import time
import asyncio
import yaml
from datetime import datetime

class TokenAnalyzer:
    def __init__(self, config_path='config.yaml'):
        print("初始化 TokenAnalyzer...")
        
        # 加载配置
        self.config = self.load_config(config_path)
        
        # 初始化API客户端
        self.init_apis()
        self.cache = {}
        self.cache_duration = 300  # 缓存5分钟
        
    def load_config(self, config_path):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print("成功加载配置文件")
            return config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            raise
        
    def init_apis(self):
        """初始化各平台API"""
        try:
            # Google API
            print("正在初始化 Google API...")
            self.google_api = build(
                "customsearch", "v1",
                developerKey=self.config['GOOGLE_API_KEY']
            )
            print("Google API 初始化成功")
            
            # # Twitter API
            # print("正在初始化 Twitter API...")
            # self.twitter_client = tweepy.Client(
            #     bearer_token=self.config['TWITTER_BEARER_TOKEN']
            # )
            # print("Twitter API 初始化成功")
            
        except Exception as e:
            print(f"API初始化失败: {e}")
            raise
            
    async def test_apis(self):
        """测试所有API是否正常工作"""
        print("\n开始测试 API 连接...")
        
        # 测试 Google API
        try:
            print("\n测试 Google API...")
            result = self.google_api.cse().list(
                q="test",
                cx=self.config['GOOGLE_SEARCH_ENGINE_ID']
            ).execute()
            
            # 添加调试信息
            print("Google API 原始返回:", result)
            
            # 安全地获取结果数量
            total_results = result.get('searchInformation', {}).get('totalResults', '0')
            print("✓ Google API 测试成功")
            print(f"测试搜索结果数量: {total_results}")
        except Exception as e:
            print(f"✗ Google API 测试失败: {e}")
            print(f"错误类型: {type(e)}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            
        # # 测试 Twitter API
        # try:
        #     print("\n测试 Twitter API...")
        #     result = self.twitter_client.search_recent_tweets(query="test")
        #     print("✓ Twitter API 测试成功")
        #     print(f"测试推文数量: {len(result.data) if result.data else 0}")
        # except Exception as e:
        #     print(f"✗ Twitter API 测试失败: {e}")
    
    async def analyze_token_mentions(self, token_address, token_name):
        """分析代币在各平台的提及情况"""
        print(f"\n开始分析代币: {token_name} ({token_address})")
        
        # 检查缓存
        if token_address in self.cache:
            cache_age = time.time() - self.cache[token_address]['timestamp']
            print(f"发现缓存数据，年龄: {cache_age}秒")
            if cache_age < self.cache_duration:
                print("使用缓存数据") 
                return self.cache[token_address]['data']
        
        tasks = [
            self.get_google_mentions(token_address),
            # self.get_twitter_mentions(token_address)
        ]
        
        print("执行API查询...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        analysis = {
            'google_mentions': results[0] if not isinstance(results[0], Exception) else 0,
            # 'twitter_mentions': results[1] if not isinstance(results[1], Exception) else 0,
            'total_score': sum(r for r in results if not isinstance(r, Exception)),
            'timestamp': time.time()
        }
        
        # 更新缓存
        self.cache[token_address] = {
            'data': analysis,
            'timestamp': time.time()
        }
        
        print(f"分析完成: {analysis}")
        return analysis

    async def get_google_mentions(self, token_address):
        """获取Google搜索结果数量"""
        print(f"获取 Google 提及度: {token_address}")
        try:
            result = self.google_api.cse().list(
                q=f'"{token_address}"',
                # cx=self.config['GOOGLE_SEARCH_ENGINE_ID']
                cx="017576662512468239146:omuauf_lfve"
            ).execute()
            
            # 添加结果调试
            print("Google 搜索原始返回:", result)
            
            # 安全地获取和转换结果
            total_results = result.get('searchInformation', {}).get('totalResults', '0')
            count = int(total_results)
            print(f"Google 提及次数: {count}")
            return count
        except Exception as e:
            print(f"Google API 错误: {e}")
            print(f"错误类型: {type(e)}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return 0

    # async def get_twitter_mentions(self, token_address):
    #     """获取Twitter提及次数"""
    #     print(f"获取 Twitter 提及度: {token_address}")
    #     try:
    #         result = self.twitter_client.search_recent_tweets(
    #             query=f'"{token_address}"',
    #             max_results=100
    #         )
    #         count = len(result.data) if result.data else 0
    #         print(f"Twitter 提及次数: {count}")
    #         return count
    #     except Exception as e:
    #         print(f"Twitter API 错误: {e}")
    #         raise

# 测试代码
async def main():
    """主函数用于测试和调试"""
    print("\n=== 开始测试 TokenAnalyzer ===")
    
    try:
        # 初始化分析器
        analyzer = TokenAnalyzer()
        
        # 测试 API 连接
        await analyzer.test_apis()
        
        # 测试代币分析
        test_token = {
            'address': 'Df6yfrKC8kZE3KNkrHERKzAetSxbrWeniQfyJY4Jpump',
            'name': 'CHILLGUY'
        }
        
        print("\n测试代币分析...")
        result = await analyzer.analyze_token_mentions(
            test_token['address'],
            test_token['name']
        )
        
        print(f"\n测试结果:")
        print(f"Google 提及: {result['google_mentions']}")
        # print(f"Twitter 提及: {result['twitter_mentions']}")
        print(f"总分: {result['total_score']}")
        
    except Exception as e:
        print(f"\n测试过程中出错: {e}")
        raise

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
