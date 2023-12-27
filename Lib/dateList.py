from calendar import monthrange

dateList = list()
stardingDate = "20100302"
endingDate = "20201111"
yearList = [i for i in range(int(stardingDate[:4]), int(endingDate[:4])+1)]

for year in yearList:
    for month in ["01","02","03","04","05","06","07","08","09","10","11", "12"]:
        for day in range(1, monthrange(year,int(month))[1]+1 ):
            day = str(day)
            if len(day) == 1:
                day = "0" + str(day)
            dateList.append(str(year)+str(month)+day)

print(dateList)


            


