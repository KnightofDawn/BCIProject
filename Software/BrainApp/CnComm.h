/*! \mainpage CnComm v1.51 ���̴߳���ͨѶ�� 
*	\section About ����
*  
*  \n �汾: CnComm v1.51
*  \n ��;: WINDOWS/WINCE ���̴߳���ͨѶ��
*  \n ����: C++ (ANSI/UNICODE)
*  \n ƽ̨: WINDOWS(WIN98/NT/2000/XP/2003/Vista); WINCE 5.0 ģ����; Pocket PC 2003 ģ����;
*  \n Ӳ��: PC����; ���ڷ�����; USB����; ���⴮��;
*  \n ����: BC++ 5(free tool); C++ BUILDER 4, 5, 6, X; EVC 4(sp4); G++ 3, 4; Intel C++ 7, 8, 9; VC++ 6(sp6), .NET, 2003, 2005;
*  \n ����: llbird
*  \n ����: wushaojian@21cn.com
*  \n ����: http://blog.csdn.net/wujian53 http://www.cppblog.com/llbird  
*  \n ά��: 2002.10 - 2009.8
*
*  \section Announce ˵��
*  \n 1) ��������ʹ�ü�����, �뱣���������;                                           
*  \n 2) ���Ƽ�ֱ���ڱ��������޸�, Ӧͨ��C++�̳���չ������չ������;                          
*  \n 3) �����ֱ���޸ı�����, �뷢һ�ݸ��ң�����ͬ���ѷ���������ĸĶ�;                              
*  \n 4) ������cnComm1.4���°汾, �кܴ�Ķ���ͬʱҲ����CnComm;
*  \n 5) �����Ǿ��ϻ�, ˮƽ����, ������������, ��ӭ����ָ��, ��������, ʱ������, ���ṩ��CnComm�ڲ����������ѯ;
*  
*  \section Log ��־
*  \n 2009 v1.51 ������; ���ǵ������Ĺ����п��ܲ����ٺʹ��ڴ򽻵�����ܿ��������һ��;
*  \n 2009 v1.5  �������÷ֿ���������; ���Ӷ�WINCE��֧��(ģ�����²���ͨ��);
*  \n 2008 v1.4  ���Ӷ�ͬ��IO�Ķ��߳�֧��; ����C++�쳣��֧��; ����CnComm; Cn == C Next;
*  \n 2007 v1.3  ϸ�ڲ����޶�;
*  \n 2006 v1.2  ϸ�ڲ����޶�;
*  \n 2005 v1.1  ϸ�ڲ����޶�;
*  \n 2004 v1.0  ����VC�������(������), �ڶ��WINDOWƽ̨������������ͨ��, �״ι�������cnComm;
*  \n 2002 v0.1  ������Ҫ��������ͨѶ������, ��ͳC++�ļ̳л���, ��ͳC�������;
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
	//! �ٽ���
	//struct	InnerLock;

	//! ��������ģʽ��ö��ֵ, 32λ����

	//! WIN32:Ĭ�ϴ򿪴���ʱ���������߳� �첽�ص���ʽ 
	CnComm()

	{
		//Init(); 
		//SetOption(dwOption);
	}
	//! ��һģʽ���� ����cnComm1~1.3 \param[in] bThread ���������߳� \param[in] bOverlapped �����ص�I/O
	CnComm(bool bThread, bool bOverlapped)
	{
		DWORD dwOption = 0;
	}
	//! ���� �Զ��رմ��� 
	virtual ~CnComm()
	{
		//Close(); 
		//Destroy();
	}

	
};

#endif //! _CN_COMM_H_
