# Robotwriter API Document

+ 目前所有的输入参数皆透过 function parser parse 完后，再传过来。robotwriter 不主动解释参数。

## APIs
分类 | 请求方式 | 接口 | 说明
-----|--------|------|-----
weather | GET | /V2/weather | 取得天气的资讯
soccer | GET | /V2/soccer | 取得足球比赛的资讯
timeinfo | GET | /V2/timeinfo | 取得日期时间的资讯

## Weather 天气 
+ 资料来源
	
	```
	每个小时自 https://content.emotibot.com 取得所有支援城市天气资讯，并存到 local 的 cache 中。
	Local cache 只会存今日与未来七日(含今日)的资讯以避免消耗过多记忆体。
	
	content.emotibot.com 的资料来源是自和风天气网付费 API，目前只有购买中国城市，未来七日(含今日)的天气资讯，包含气温，风力，即时空气质量(AQI)，三天生活指数。
	```

+ 端口	
	
	```GET /V2/weather```

+ 请求参数

	栏位 | 类型 | 必要 | 预设值 | 说明
	-----|-----|-----|-------|-----
	city_name | string | 否 | 无 | 欲查询的城市名称，目前只有支援中国城市，且不支援省份
	date | string | 否 | 今日 | 欲查询的日期，格式 YYYYMMDD
	time_name | string | 否 | 无 | 用来组成回复语的日期名称，如「今天」、「下周一」
	keywords | string | 否 | 无 | 查询关键字，目前支授「温度、气温、雨、伞、pm2.5、霾、雾霾、雪、风」
	gender | string | 否 | 无 | 支援「男」/「女」，若为女，则回覆语有可能挑选到紫外线相关的建议语 
	days | int | 否 | 1 | 欲查询的日期天数，则 days 需传入 2；该参数要生效，date 必须是未来日期
	
+ 回覆

	```
	{
		"answer": "[上海阴，全天15℃~21℃，当前21℃。中级风，小心迷伤眼睛。空气略有污染，要戴防雾霾口罩，告诉老人和孩子减少出行。],[拼却挥汗如雨的春和夏，终于迎来岁月如歌的秋高气爽好天气~]",
		"statusCode": 200
	}
	```	
	
+ 回覆参数

	栏位 | 类型 |  说明
	----|------|----- 
	answer | string | 天气资讯或例外发生时的例外状况日志
	statusCode | int | 处理的状态码，成功为 200，失败或是异常状况发生时为 500
	
+ 笵例

	+ 未给任何参数
	
	```
	curl -XGET http://{IP}:10101/V2/weather
	
	{
  		"answer": "小影不知道你的地点呢，在句子中加上地点再问小影一次吧~\n\n像「北京天气」、「上海明天会不会下雨」，这些小影都看得懂喔！",
  		"statusCode": 200
	}
	```
	
	+ 只给 city_name
	
	```
	curl -XGET http://{IP}:10101/V2/weather?city_name=上海
	
	{
  		"answer": "[上海阴，全天15~21度，当前21℃。中级风，当心尘土迷到眼睛。空气中度污染，AQI为156，记挂你的身体，防雾霾口罩戴起来。],[明日天气多云，13~22度，中级风，风力2级。]",
  		"statusCode": 200
	}
	```
	
	+ 找不到 city_name 

	```
	curl -XGET http://{IP}:10101/V2/weather?city_name=海南  # 海南是省份
	
	{
  		"answer": "暂未找到海南天气，可以告诉我具体城市吗？如“北京天气”",
  		"statusCode": 200
	}
	```
	
	+ 取得关键字相关天气

	```
	# 上海今天会下雨吗
	curl -XGET http://{IP}:10101/V2/weather?city_name=上海&keywords=雨&time_name=今天
	
	{
  		"answer": "[今天不会下雨，当然不用带伞了，啦啦啦~],[完整预报：上海阴，中级风，小心迷伤眼睛。气温15℃~21℃，现在21℃。空气中度污染，AQI为156，牵挂你的健康，出行戴上防雾霾口罩吧。]",
  		"statusCode": 200
	}
	
	# 上海今天空气质量如何
	curl -XGET http://{IP}:10101/V2/weather?city_name=上海&keywords=霾&time_name=今天&date=20171107
	
	{
  		"answer": "[今天AQI指数是30。],[完整预报：广州中雨，气温17℃~22℃，此刻20℃。中级风，注意尘土飞扬。空气质量超赞，心旷神怡啊！带伞带伞，可以遛没带伞的妹子回来！]",
  		"statusCode": 200
	}
	```
	
	+ 取得末来 n 天天气资讯

	```
	# today is 20171107，找自20171108开始7天的天气资讯
	curl -XGET http://{IP}:10101/V2/weather?city_name=上海&days=7&date=20171108
	
	# 未来只支援7天(包含今日，找不到的天气则不会返回，该例中 20171114找不到则不会返回)
	{
  		"answer": "上海星期三多云，13~22度，中级风，风力2级；周四多云，15℃~20℃，中级风，风力2级；周五晴，11~19度，中级风，风力2级；周六晴，11℃~16℃，中级风，风力2级；周天晴，12℃~17℃，中级风，风力2级；星期一晴，14~18度，中级风，风力2级；",
  		"statusCode": 200
	}
	
	# 上海周末天气 (today is 20171107)
	curl -XGET http://{IP}:10101/V2/weather?city_name=上海&days=2&date=20171111&time_name=周末
	
	{
  		"answer": "上海周六晴，11~16度，中级风，风力2级；星期日晴，12℃~17℃，中级风，风力2级。",
  		"statusCode": 200
	}	
	```
	
## 足球 (soccer)
TBD

## 时间 (timeinfo)
TBD