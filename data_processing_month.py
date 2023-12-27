from calendar import monthrange
from Lib.id import index, index_pickle
from Lib.eventCode import eventBaseCodeList, eventRootCodeList
import os
import time
import pickle
import math


index = index_pickle

def printAndLog(content):
    print(content)
    if not os.path.exists("logfiles"):
        os.makedirs("logfiles")
    currentDate = time.strftime("%Y-%m-%d")
    with open(f"logfiles//{currentDate}.log", "a", encoding = "UTF-8") as f:
        print(time.asctime()+"\t"+content, file = f)

def readf(filepath):
    print("\tReading data from", filepath)
    startTime = time.time()
    with open(filepath, "r", encoding = "UTF-8") as f:
        f = f.read()
        f = f.strip().splitlines()
    print("\tStart formatting...")
    mylines = list()
    # lineNumber = len(f)
    # lineCount = 0
    for line in f:
        myline = list()
        for word in line.split("\t"):
            myline.append(word)
        mylines.append(myline)
        # print(f"\t{myline[1]}", "\r", end = "")
        # lineCount += 1
        # print(f"\t{str(lineCount*100/lineNumber)[:5]}%", "\r", end = "")
    endTime = time.time()
    timeSpent = round(endTime-startTime, 2)
    print(f"\tData reading and formatting finished in {timeSpent} seconds.")
    return mylines

def readPickle(filepath):
    startTime = time.time()
    print("\tLoading pickle data from", filepath)
    with open(filepath, "rb") as f:
        data = pickle.load(f)
    endTime = time.time()
    timeSpent = round(endTime-startTime, 2)
    print(f"\tPickle loading finished in {timeSpent} seconds.")
    return data



def savef(filepath, data):
    print("\tSaving data to", filepath)
    data = [str(i) for i in data]
    with open(filepath, "a", encoding = "UTF-8") as f:
        data = "\t".join(data)
        print(data, file = f)
    printAndLog(f"Record: data successfully saved to {filepath}.")
        

def calInteractionVal(dayData, actor1, actor2):
    print("\tCalculating interactionVal...")
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
        if line[index["Actor1CountryCode"]] == actor2:
            actor2CountTotal += 1
            if line[index["Actor2CountryCode"]] == actor1:
               actor2CountActor1 += 1  
    countActor1AndActor2 += actor1CountActor2 + actor2CountActor1
    interactionVal = (countActor1AndActor2*actor2CountActor1*actor1CountActor2*1000000)/(countTotal*actor1CountTotal*actor2CountTotal)
    print("\tFinished calculating interactionVal.")
    return interactionVal

def refine(dayData, actor1, actor2):
    print(f"\tRefining data...")
    myDayData = list()
    for line in dayData:
        if line[index["Actor1CountryCode"]] == actor1 and line[index["Actor2CountryCode"]] == actor2:
            myDayData.append(line)
    return myDayData

def decay(input, n, base = 1):
    """
    n为函数常数项，默认值为 1， 该值越大衰减越快，一般该值由窗口长度决定\n
    base为另外一个常数项，该值越大衰减越快，一般该值要根据对衰减度的要求指定
    """
    return (base*math.e)**(-n*input)

def calMonthAverage(data):
    count = 0
    value = float()
    for i in data:
        scale = i[index["GoldsteinScale"]]
        if scale == "": scale = float()
        value += float(scale)
        count += 1
    return value/count

def calRelationVal(windowData, flag = 3):
    """
    flag = 0 计算的是关系印象值\n
    flag = 1 采用事件积累说，计算的是关系积累值\n
    flag = 2 采用关系反映说， 计算的是深层关系值\n
    flag = 3 窗口内的数据的单纯加权平均， 计算的是关系参考值\n
    flag = 4 不考虑窗口,进行当月数据的加权平均， 计算的是事件平均值\n
    flag = 99 不考虑窗口，进行当月数据的不同事件数量统计
    """
    startTime = time.time()
    windowLength = len(windowData)
    decayConst = float() 
    decayConst = math.log(0.1, math.e)/-(windowLength - 1) #根据窗口长度指定衰减函数的常量


    
    relationVal = float()
    if flag == 0:
        count = int()
        result = float()
        for data in windowData[::-1]:
            average = calMonthAverage(data)
            result += average * decay(count, decayConst)
            count += 1
        relationVal = result
    elif flag == 1:
        count = int() #count loop
        result = float()
        for data in windowData[::-1]:
            eventValCount = dict()    
            for line in data:
                scale = line[index["GoldsteinScale"]]
                if scale == "": scale = float()
                value = float(scale)

                if value in eventValCount.keys():
                    eventValCount[value] += 1
                else:
                    eventValCount[value] = int()
            totalCount = 0
            for count in eventValCount.values():
                totalCount += count
            
            eventValRatio = dict(zip(list(eventValCount.keys()), [0 for i in range(len(eventValCount.values()))]))
            for item in eventValCount.items():
                eventValRatio[item[0]] = item[1]/totalCount
            
            for item in eventValRatio.items():
                eventRatio = item[1]
                eventValue = item[0]
                if eventValue == 0: #不计入计算，否则会引发devidedByZero错误
                    continue
                else:
                    base = 10/abs(eventValue) #指定base常量. evenValue作为分母可以令分值绝对值越大的事件影响事件更长
                    amplify = 1#如果有必要，可以对base值进行适当的增幅。
                    base /= amplify
                    decayVal = decay(count, decayConst, base = base)
                    result += (eventRatio * eventValue * decayVal)
                if result < -10000:
                    raise Exception()
            count += 1
        relationVal = result
    
    elif flag == 2:
        plusValue = calMonthAverage(windowData[-1])
        minusValue = float()
        count = 1
        for data in windowData[-2::-1]:
            average = calMonthAverage(data)
            minusValue += average * decay(count, decayConst, base = windowLength-1 ) #对将base的值与windowLength-1的值进行统一
            count += 1
        relationVal = plusValue-minusValue

    elif flag == 3:
        totalVal = int()
        for data in windowData:
            val = float()
            count = int()
            for line in data:
                scale = line[index["GoldsteinScale"]]
                if scale == "": scale = float()
                val += float(scale)
                count += 1
            totalVal += val/count
        relationVal = totalVal/windowLength

    elif flag == 4:
        val = float()
        count = int()
        for line in windowData[-1]:
            scale = line[index["GoldsteinScale"]]
            if scale == "": scale = float()
            val += float(scale) 
            count += 1
        relationVal = val/count

    elif flag == 99:
        eventBaseCodeDict = dict(zip(eventBaseCodeList, [0 for i in range(len(eventBaseCodeList))]))
        eventRootCodeDict = dict(zip(eventRootCodeList, [0 for i in range(len(eventRootCodeList))]))
        eventQuadCodeDict = dict(zip(["1","2","3","4"],[0,0,0,0]))
        eventCount = 0
        for line in windowData[-1]:
            eventCount += 1
            eventBaseCode = line[index["EventCode"]][:3]
            eventRootCode = line[index["EventRootCode"]]
            eventQuadCode = line[index["QuadClass"]]
            eventBaseCodeDict[eventBaseCode] += 1
            eventRootCodeDict[eventRootCode] += 1
            eventQuadCodeDict[eventQuadCode] += 1
        
        content1 = list(eventBaseCodeDict.values())
        content2 = list(eventRootCodeDict.values())
        content3 = list(eventQuadCodeDict.values())
        content = [eventCount]+content1+content2+content3

        header1 = list(eventBaseCodeDict.keys())
        header1 = ["BaseCode_"+i for i in header1]
        header2 = list(eventRootCodeDict.keys())
        header2 = ["RootCode_"+i for i in header2]
        header3 = list(eventQuadCodeDict.keys())
        header3 = ["QuadCode_"+i for i in header3]
        header = ["Total"]+header1+header2+header3
        endTime = time.time()
        print(f"\tCounting finished in {round(endTime-startTime, 2)} seconds.")
        return header, content

        


    else:
        raise Exception("Unexpected flag value")
    endTime = time.time()
    return relationVal



def calVal(monthList, actorsGroup, windowLength = 3):
    actorTuples = set() #确定的双边关系群
    combGroup = list() #需要进行组合和国家群
    for actors in actorsGroup:
        if type(actors) == list:
            actorTuples.add(tuple(actors))
            actorTuples.add(tuple(actors[::-1]))
        else:
            combGroup.append(actors)
    for actor1 in combGroup:
        for actor2 in combGroup:
            actorTuples.add(tuple([actor1, actor2]))


    

    for actor1, actor2 in actorTuples:
        windowData = []
        interactionValSerial = dict()
        relationValSerial = dict()

        print(f"Entering the loop for {actor1} to {actor2}")
        savingRelValFilePath = savingDir + "relationValue.csv"
        savingEventCountFilePath = savingDir + actor1 + "_" + actor2 + "_event.csv"
        for month in monthList:
            dataFilePath = dataDir+month+".pickle"

            if len(windowData) <= windowLength:
                print("\n\tFilling window...")
                data = readPickle(dataFilePath)
                interactionVal = calInteractionVal(data, actor1, actor2)
                data = refine(data, actor1, actor2)
                windowData.append(data)
                interactionValSerial[month] = interactionVal

            if len(windowData) == windowLength:
                print("\tCalculating relationVal for", month)
                relationVal = [calRelationVal(windowData, flag = 0), 
                               calRelationVal(windowData, flag = 1),
                               calRelationVal(windowData, flag = 2),
                               calRelationVal(windowData, flag = 3),
                               calRelationVal(windowData, flag = 4),
                               interactionVal]
                eventCountHeader, eventCount = calRelationVal(windowData, flag = 99)
                trash = windowData.pop(0)
                trash = None
                print("\tResult being", relationVal)
                headerFileName = "headerFile.csv"
                if headerFileName not in os.listdir(savingDir):
                    savef(savingDir+headerFileName, ["yearmonth","actor1","actor2"]+eventCountHeader)
                    savef(savingDir+headerFileName,["yearmonth","actor1","actor2"]+["impressionVal","accumulativeVal","deepVal","windowMeanVal","meanVal", "interactionVal"])

                savef(savingRelValFilePath, [month,actor1,actor2]+relationVal)
                savef(savingEventCountFilePath, [month,actor1,actor2]+eventCount)
                relationValSerial[month] = relationVal

        for i,j in list(zip(interactionValSerial.items(),relationValSerial.items())):
            print(i[0], i[1], j[1], sep ="\t")



dataDir = "Pickle\\"
savingDir = "OrderedData\\"
monthList = list()
for year in range(2000,2024):
    for month in range(1,13):
        year = str(year)
        month = str(month)
        if len(month) == 1:
            month = "0" + month
        monthList.append(year+month)
monthList = monthList[:-7]
# monthList = ["201505","201506","201507"]
print(f"monthList is {monthList}")
# windowLength = int()
calVal(monthList, [["CHN", "RUS"]])

