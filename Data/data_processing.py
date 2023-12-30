from Lib.id import *
from calendar import monthrange
dataDir = "CleanData\\"
def readf(filepath):
    print("Reading data from", filepath)
    with open(filepath, "r", encoding = "UTF-8") as f:
        f = f.read()
        f = f.strip().splitlines()
    mylines = list()
    for line in f:
        myline = list()
        for word in line.split("\t"):
            myline.append(word)
        mylines.append(myline)
    print("Data reading and formatting finished.")
    return mylines

def readDay(monthData, day):
    dayData = list()
    for line in monthData:
        if line[index["SQLDATE"]] == day:
            dayData.append(line)
        elif dayData != []:
            break
    if dayData == []:
        raise Exception
    return dayData

def interactionValCal(dayData, actor1, actor2):
    actor1CountTotal = 0
    actor2CountTotal = 0
    actor1CountActor2 = 0
    actor2CountActor1 = 0
    countTotal = len(dayData)
    countActor1AndActor2 = 0
    for line in dayData:
        if line[index["Actor1CountryCode"]] == actor1:
            actor1CountTotal += 1
            if line[index["Actor2CountryCode"]] == actor2:
                actor1CountActor2 += 1
        elif line[index["Actor1CountryCode"]] == actor2:
            actor2CountTotal += 1
            if line[index["Actor2CountryCode"]] == actor1:
               actor2CountActor1 += 1  
    countActor1AndActor2 += actor1CountActor2 + actor2CountActor1
    interactionVal = countTotal*actor1CountTotal*actor2CountTotal*100/(countActor1AndActor2*actor2CountActor1*actor1CountActor2)
    return interactionVal

def refine(dayData, actor1, actor2):
    myDayData = list()
    for line in dayData:
        if line[index["Actor1CountryCode"]] == actor1 and line[index["Actor2CountryCode"]] == actor2:
            myDayData.append(line)
    return myDayData

def process(windowData):
    print("Start processing data...")
    dataList = list()
    for dayData in windowData:
        eventCount = 0
        totalScore = float()
        for line in dayData:
            eventCount += 1
            totalScore += float(line[index["GoldsteinScale"]])
        dayVal = totalScore/eventCount
        dataList.append(dayVal)
    totalVal = float()
    count = 0
    for val in dataList:
        totalVal += val
        count += 1
    print("Finished processing data. Data being", totalVal/count)
    return totalVal/count

def mkDateList(start, end):
    start = str(start)
    end = str(end)
    dayList = []
    for year in range(int(start[:4]),int(end[:4])+1):
        for month in ["01","02","03","04","05","06","07","08","09","10","11","12"]:
            for date in range(1, monthrange(year, int(month))[1]+1):
                date = str(date)
                if len(date) == 1:
                    date = "0"+date
                dayList.append(str(year)+str(month)+str(date))
    # print(dayList)
    return dayList



actorList = list([("CHN","USA")])
timeList = list()
timeUnit = str() #就是一天
windowSize = 10
relationCalMethod = str()
#检查actorList是否合法
#检查timeList是否合法

relationVal = int()
interactionVal = int() #domestic_ratio_1*domestic_ratio_2*international_ratio

#结果可以生成两种数据文件。
#一种是将单位时间内的值量化为单一数字之后将所有双边关系在全时段当中的表现汇集的数据文件
#一种是将单位时间内的事件按照事件类型进行统计之后将一对双边关系在两个方向的全时段当中的表现汇集而成的数据文件

dayList = list()
dayList = mkDateList(2014, 2015)
monthList = list(set([i[:6] for i in dayList]))
monthList.sort()
print(monthList)
windowData = list()

month = monthList.pop(0)    
monthData = readf(dataDir+month+".txt")

for actorTuple in actorList:
    if actorTuple[0] != actorTuple[1]:
        interactionVal = int()
        for actor1, actor2 in [actorTuple,actorTuple[::-1]]:    
            relationVal = list()
            for day in dayList:
                if day[:6] == month:
                    dayData = readDay(monthData, day)
                else:#日子不在当前month数据当中，更新month和monthData
                    month = monthList.pop(0) 
                    monthData = readf(dataDir+month+".txt")
                    dayData = readDay(monthData, day)
                
                if interactionVal == 0:
                    interactionVal = interactionValCal(dayData, actor1, actor2)
                    print("Interaction Value is", interactionVal)

                dayData = refine(dayData, actor1, actor2)
                windowData.append(dayData)
                if len(windowData) == windowSize:
                    relationVal.append(process(windowData))
                    print("Date is", day)
                    windowData.pop(0)
                elif len(windowData) < windowSize:
                    print("Filling the window...")
                    continue
            print(relationVal)

    else:#actor1和actor2是一个行为体
        pass

