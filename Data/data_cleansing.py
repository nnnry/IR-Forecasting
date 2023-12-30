import os
import time
import re

objectFilePath = "CleanData"
sourceFilePath = "Source"
if not os.path.exists(objectFilePath):
    os.makedirs(objectFilePath)
    print("Created directory", objectFilePath)

allowedDateError = 31

filenameList = os.listdir(sourceFilePath) #可能用到的函数 os.listdir()
dateList = []
for item in filenameList:
    item = item.split(".")[0]
    dateList.append(item)

date2filename = dict(zip(dateList, filenameList))
print(f" {list(date2filename.items())[0:-1:5]} \nPlease check if matchs are correct y/n:")
if input() == "y":
    print("Confirmed. Continue processing...")


def printAndLog(content):
    print(content)
    if not os.path.exists("logfiles"):
        os.makedirs("logfiles")
    currentDate = time.strftime("%Y-%m-%d")
    with open(f"logfiles//{currentDate}.log", "a", encoding = "UTF-8") as f:
        print(time.asctime()+"\t"+content, file = f)

def CleansDataAlsoPopAndSaveTheFirst(dataDict):
    #Clean data
    cleanseTargetDate = list(dataDict.keys())[0]
    prossessingDateList = list(dataDict.keys())
    cleanData = list()
    modificationCount = dict()
    modificationCount["moved out"] = 0
    modificationCount["moved in"] = 0
    modificationCount["deleted"] = 0
    dateCord = 1
    for keyDate in dataDict.keys():
        if keyDate == cleanseTargetDate: #处理第一个数据文件
            for line in dataDict[cleanseTargetDate]: 
                if line[dateCord] == cleanseTargetDate:  # 数据日期符合文件日期
                    cleanData.append(line)
                elif line[dateCord] in prossessingDateList: #数据日期不符合文件日期，但缓存文件中有对应的
                    lineDate = line[dateCord]
                    dataDict[lineDate].append(line)
                    modificationCount["moved out"] += 1
                    # print(f"This is what being modified under the filedate {keyDate}:\n", line[:5])
                else:
                    # print(f"This is what being removed under the filedate {keyDate}:\n",line[:5])
                    modificationCount["deleted"] += 1
        else: #处理第一个以外的数据文件，只需要将属于第一个数据文件的数据返回给它就可以
            for line in dataDict[keyDate]:
                if line[dateCord] == cleanseTargetDate:
                    cleanData.append(line)
                    modificationCount["moved in"] += 1
                    # print(f"This is what being modified under the filedate {keyDate}:\n", line[:5])
    printAndLog(f"Record: {modificationCount['moved out']} moving-out, {modificationCount['moved in']} moving-in and {modificationCount['deleted']} deletes made while the cleansing of {cleanseTargetDate} day data.")

    #Pop and save
    dataDict.pop(cleanseTargetDate)
    cleanseTargetMonth = cleanseTargetDate[:6]
    with open(objectFilePath+"\\"+cleanseTargetMonth+".txt", "a", encoding = "UTF-8") as f:
        for i in cleanData:
            print("\t".join(i), file = f)

def readData(date):
    with open(sourceFilePath+"//"+date2filename[date], "r") as f:
        lines = f.read().splitlines()
    newlines = []
    for line in lines:
        line = line.split("\t")
        myline=[]
        count = 0
        for item in line:
            if count in [0,1,4,6,7,12,15,16,17,22,26,28,29,30,33,34]:#指定需要保留的数据项的index，请根据需求进行更改
                if line.index(item)==34:item=item[0:7]#aveTone只取4个小数
                myline.append(item)
            elif count == 57:#只保留网址的开头，若不是网址的情况全部保留
                if "http" in item:
                    myline.append(item.split("/")[2])
                else:
                    myline.append(item)
            else:
                myline.append("")
            count += 1
        newlines.append(myline)

    return newlines

def cleanDailyUpdatedData(dateList):
    #数据清理
    #目标：将错置的日期数据放回正确的位置中
    #情况一：数据的位置错了     处理：更换位置
    #情况二：数据的日期错了     处理：删除
    #如何判断错置的数据和错误的数据？
    #现行基准：误差在+-一个月以上判断为数据的日记标记错误，可根据误差需求更改allowedDateError
    if dateList == []: 
        print("No prescribed data for date-based data to process.")
        return #如果列表为空，则退出函数
    dataBufferDict= dict()
    for date in dateList:
        print(f"Entering data loop for {date}...")
        # if date == "20130418":
        #     print("here")
        #     time.sleep(10)
        # print(date, dateList[-1])
        if (len(dataBufferDict) == allowedDateError) & (date != dateList[-1]):  # 数据buffer等于31，需要读取，清洗，删除，存储

            #数据buffer达到31个，开始清洗
            CleansDataAlsoPopAndSaveTheFirst(dataBufferDict)
            #给元数据字典补充新元素
            dataBufferDict[date] = readData(date)
            print(f"\tBuffer field updated data for {date}.")
        else:#数据buffer少于31个
            if date != dateList[-1]:#并非最后一个循环，说明刚开始读取文件，只需要读取，不需要清洗，删除，存储
                print("\tFilling buffer field...")
                #添加数据到数据列表中
                dataBufferDict[date] = readData(date)
                print(f"\tBuffer field updated data for {date}.")
        
            else:  # 进入了最后一个循环，即数据文件已读取完毕，因此只需要清洗，删除，存储，不需要读取
                print("Entering last loop...")
                dataBufferDict[date] = readData(date)
                print(f"\tBuffer field updated data for {date}.")
                lenth = len(dataBufferDict)
                for i in range(lenth):
                    CleansDataAlsoPopAndSaveTheFirst(dataBufferDict)

def cleanMonthlyData(dateList):
    #清理按月份为单位存储的数据
    for month in dateList:
        monthData = readData(month)
        cleanMonthData = list()
        for line in monthData:
            if month == line[1][:6]:
                cleanMonthData.append(line)
            else:
                printAndLog(f"record: data being removed for having mismatched date of {line[1]}.")
        with open(objectFilePath+"\\"+month+".txt", "w", encoding = "UTF-8") as f:
            for i in cleanMonthData:
                print("\t".join(i), file = f)
        printAndLog(f"record: data for {month} have been successfully updated.")

def cleanAnnualData(dateList):
    for year in dateList:
        yearData = readData(year)
        for month in ["01","02","03","04","05","06","07","08","09","10","11","12"]:
            cleanMonthData = list()
            for line in yearData:
                if line[1][:6] == year+month:
                    cleanMonthData.append(line)
            with open(objectFilePath+"\\"+year+month+".txt", "w", encoding = "UTF-8") as f:
                for i in cleanMonthData:
                    print("\t".join(i), file = f)
            printAndLog(f"record: data for {year+month} have been successfully updated.")
            
    #清理年份为单位存储的数据

ifMonthData = 0
ifAnnualData = 0
ifDailyData = 0
countIndex = 0
dailyDataList = list()
monthlyDataList = list()
annualDataList = list()
for i in dateList:
    if len(i) == 8:
       dailyDataList.append(i)
    elif len(i) == 6:
        monthlyDataList.append(i)
    elif len(i) == 4: 
        annualDataList.append(i)
print(annualDataList)
print(monthlyDataList)
cleanAnnualData(annualDataList)
cleanMonthlyData(monthlyDataList)
cleanDailyUpdatedData(dailyDataList)
