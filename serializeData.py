from os import listdir
import pickle
from Lib.id import list_pickle, index_pickle

dataDir = ["CleanData\\", "NewCleanData\\"]
saveTo = "Pickle\\"

for dir in dataDir:
    filePathList = [dir+filename for filename in listdir(dir)]
    for file in filePathList:
        filename = file.split("\\")[1].split(".")[0]
        print("filename of current loop is", filename)
        with open(file, "r", encoding = "UTF-8") as f:
            data = f.read()
            data = data.strip().splitlines()
            print("Data read in.")
        mydata = list()
        for line in data:
            myline = list()

            count = 0
            for word in line.split("\t"):
                if count in list_pickle:
                    myline.append(word)
                count += 1

            mydata.append(myline)
        print(mydata[:10])
        print("Data split.")
        data = None

        with open(f"{saveTo+filename}.pickle", "wb") as f:
            pickle.dump(mydata, f)
            print(f"Data dumped in file {filename}.pickle.")
