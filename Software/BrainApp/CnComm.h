/*! \mainpage CnComm v1.51 多线程串口通讯库 
*	\section About 关于
*  
*  \n 版本: CnComm v1.51
*  \n 用途: WINDOWS/WINCE 多线程串口通讯库
*  \n 语言: C++ (ANSI/UNICODE)
*  \n 平台: WINDOWS(WIN98/NT/2000/XP/2003/Vista); WINCE 5.0 模拟器; Pocket PC 2003 模拟器;
*  \n 硬件: PC串口; 串口服务器; USB串口; 虚拟串口;
*  \n 编译: BC++ 5(free tool); C++ BUILDER 4, 5, 6, X; EVC 4(sp4); G++ 3, 4; Intel C++ 7, 8, 9; VC++ 6(sp6), .NET, 2003, 2005;
*  \n 作者: llbird
*  \n 邮箱: wushaojian@21cn.com
*  \n 博客: http://blog.csdn.net/wujian53 http://www.cppblog.com/llbird  
*  \n 维护: 2002.10 - 2009.8
*
*  \section Announce 说明
*  \n 1) 可以自由使用及传播, 请保留相关声明;                                           
*  \n 2) 不推荐直接在本代码上修改, 应通过C++继承扩展机制扩展本代码;                          
*  \n 3) 如果您直接修改本代码, 请发一份给我，便于同网友分享您有益的改动;                              
*  \n 4) 不兼容cnComm1.4以下版本, 有很大改动，同时也更名CnComm;
*  \n 5) 还是那句老话, 水平有限, 错误在所难免, 欢迎来信指正, 收入有限, 时间有限, 不提供除CnComm内部问题外的咨询;
*  
*  \section Log 日志
*  \n 2009 v1.51 修正版; 考虑到将来的工作中可能不会再和串口打交道，这很可能是最后一版;
*  \n 2009 v1.5  增加内置分块链表缓冲区; 增加对WINCE的支持(模拟器下测试通过);
*  \n 2008 v1.4  增加对同步IO的多线程支持; 增加C++异常的支持; 改名CnComm; Cn == C Next;
*  \n 2007 v1.3  细节部分修订;
*  \n 2006 v1.2  细节部分修订;
*  \n 2005 v1.1  细节部分修订;
*  \n 2004 v1.0  采用VC命名风格(匈牙利), 在多个WINDOW平台、编译器测试通过, 首次公开发布cnComm;
*  \n 2002 v0.1  因工作需要开发串口通讯基础类, 传统C++的继承机制, 传统C命名风格;
*/

#ifndef _CN_COMM_H_
#define _CN_COMM_H_

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
#include <tchar.h>


class CnComm    
{
public:
	//! 临界区
	//struct	InnerLock;

	//! 用于配置模式的枚举值, 32位掩码

	//! WIN32:默认打开串口时启动监视线程 异步重叠方式 
	CnComm()

	{
		//Init(); 
		//SetOption(dwOption);
	}
	//! 另一模式构造 兼容cnComm1~1.3 \param[in] bThread 启动监视线程 \param[in] bOverlapped 启用重叠I/O
	CnComm(bool bThread, bool bOverlapped)
	{
		DWORD dwOption = 0;
	}
	//! 析构 自动关闭串口 
	virtual ~CnComm()
	{
		//Close(); 
		//Destroy();
	}

	
};

#endif //! _CN_COMM_H_
