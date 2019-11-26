# 接口自动化框架使用注意事项

1、工程结构：
    1）excel_config：存放数据来源Excel、Excel操作函数（excel_data.py中附带少数变量处理的重要函数）；
    2）preinfo_config：存放cookie/token获取及处理方法（set_cookie.py/set_token.py）、
                        接口配置及请求相关函数（preactions.py/interface_config.py）、
                        文件间全局变量处理方法（global_config.py）、
                        cookie存放文件（cookie.txt）；
    3）interface：存放案例脚本文件；
    4）report：存放执行报告；
    5）db_fixture：存放数据库操作方法，目前只适用于mysql，
        db_config.ini：配置数据库基本信息；
    5）run_tests.py：执行程序入口文件、
        HTMLTestRunner.py：执行报告配置文件。

2、Excel管理注意事项：
    1）格式规范：
        a.“案例汇总”和“数据表”为固定sheet，分别用于存放单条完成流程的基础、执行信息及自动化数据信息；
        b.“案例规范”sheet中“A-G”列为固定列，“数据表”sheet中“A-F”列为固定列。
    2）维护规范：
        a.“案例汇总”、“数据表”和“Test*.py”文件中对应信息须一致，否则无法定位；
        b.步骤sheet存放案例及接口数据，“数据表”sheet主要存放请求数据。

3、框架使用技巧：
    1）“数据表”sheet中写值控制：
        在流程最后一个案例（“Test*.py”文件中最后一个def）中，须赋 myRow 为 self.myRow：
            “writeTextResult(self.testResult,caseName,myRow=self.myRow)。

    2）选定执行范围：
        run_tests.py中控制变量 loopTime，对应执行“数据表”sheet中状态为“未使用”的流程数据。
        数据不足时，流程会自动终止，pycharm中提示：
            “********** 已无足够可用数据，数据用完后执行终止! **********”。

    3）跳过流程中某案例：
        原则上“数据表”sheet中该案例下所有数据均不填则跳过，实际情况中部分案例会分为“登陆”和“交易”两部分。
        存在“登陆”情况，在用 makeJsonData 获取登陆请求最后一个参数时，whetherToInitialize 赋“是”，若登陆信息为空，则跳过；
        无“登陆”情况，同理在脚本中通过交易请求中最后一个参数取值控制。

    4）返回值控制：
        返回值列在“数据表”sheet中对应列表头带“#”，脚本中用 loadProcessValue 控制。

    5）检查执行报告（调试）：
        执行结束后“数据表”sheet中对应行会自动匹配报告文件名信息，报告覆盖单条执行流程，脚本中的打印、报错信息均在报告显示。
		
	6）“../interface/”下为当前执行范围，不执行的案例脚本，执行前先移到“../interface/可执行案例脚本/”下。

4、不足：
    1）案例报错后，流程会继续执行直至结束（已优化）；
