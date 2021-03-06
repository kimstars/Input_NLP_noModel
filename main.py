from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, Body, Request, Form,UploadFile,File
import requests
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from bson.objectid import ObjectId
import numbering
import pymongo
import uuid
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import datetime
from bs4 import BeautifulSoup
import urllib.request
import ggapi

load_dotenv()

myclient = pymongo.MongoClient(os.environ.get("DB_URL"))

mydb = myclient["NLPdataBase"]
collection = mydb["database"]


class ANS(BaseModel): 
	text : str
	answer_start : int

class QAS(BaseModel) :
	question : str
	id : str
	answer : ANS

class data(BaseModel) : 
	content : str
	qas: list
 
class NEWS(BaseModel): 
	content : str
	qas : list

 
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def form_delete(request: Request):
    colname = mydb.list_collection_names()
    print(colname)
    return templates.TemplateResponse("index.html", {"request": request, "CollectionName":colname})

@app.post('/')
async def createCollection(request: Request, colname: str  = Form(...), ip: str = Form(...)):
    print(colname) 
    time = datetime.datetime.now()
    collection = mydb[colname]
    create_time = {"name": colname, "time create": time, "ip": ip}
    x = collection.insert_one(create_time)
    colname = mydb.list_collection_names()
    return templates.TemplateResponse("index.html", {"request": request, 
                                                     "CollectionName":colname})



        
@app.post("/display", response_class=HTMLResponse)
def loadData(request: Request, nameCollection:str = Form(...) ):
    colname = mydb.list_collection_names()
    collection = mydb[nameCollection]
    li = list(collection.find())
    size = len(li)
    print(colname)
    tieude = "Xem t???t c??? data ???? nh???p t??? collection "+ nameCollection
    return templates.TemplateResponse("displayData.html", {
        "request": request, 
        "size" : size,
        "jsonData" : li,
        "tieude" : tieude,
        "CollectionName":colname,   
        "nameCollection":nameCollection,
})




def MainProcess(collection, content, listQuestion , listAnswer):# t???o data v?? th??m v??o db
    listContent = numbering.contentToList(content)
    listQAS = list()
    for i in range(len(listAnswer)):
        answer = listAnswer[i]
        question = listQuestion[i]
        start = numbering.findSentence(answer,listContent)
        objAnswer = ANS(
            text = answer,
            answer_start = start
        )
        id = (uuid.uuid4().hex)
        objQuestionAndAnswer = QAS(
            question = question,
            id = id,
            answer = objAnswer
        )
        listQAS.append(objQuestionAndAnswer.dict())
    print(len(listQAS))
    newData = data(
        content = content,
        qas = listQAS
    )
    print(collection)
    collection.insert_one(newData.dict())
    return (newData.dict())

@app.get("/home", response_class=HTMLResponse)
def write_home(request: Request):
    colname = mydb.list_collection_names()
    user_name = "MTA NLP TEAM"
    return templates.TemplateResponse("home.html", {"request": request,
                                                    "username": user_name,
                                                    "CollectionName":colname,
                                                    })

@app.post('/home')
async def handle_form(request: Request,content : str = Form(...), qas : list = Form(...), nameCollection:str = Form(...)):
    colname = mydb.list_collection_names()
    collection = mydb[nameCollection]
    listQuestion = numbering.createListQuestion(qas) 
    listAnswer = numbering.createListAnswer(qas)
    user_name = "Up th??nh c??ng nh??"
    MainProcess(collection, content, listQuestion, listAnswer)
    return templates.TemplateResponse("home.html", {"request": request,
                                                    "username": user_name,
                                                    "CollectionName":colname,
                                                    })


@app.get("/display-data", response_class=HTMLResponse)
def loadGetAllData(request: Request):
    colname = mydb.list_collection_names()
    tieude = "Xem t???t c??? data ???? nh???p"
    return templates.TemplateResponse("displayData.html", {
        "request": request, 
        "tieude" : tieude,
        "CollectionName":colname,
        })
    
    


@app.get("/delete/{id}/{nameCollection}")
async def form_delete(request: Request, id : str, nameCollection : str):
    collection = mydb[nameCollection]
    myquery = {"_id":  ObjectId(id)}
    li = collection.find_one(myquery)
    content = li['content']
    qas = li['qas']
    tieude = "Xem l???i data ???? x??a"
    collection.delete_one(myquery)
    
    return templates.TemplateResponse("delete.html", {"request": request,
                                                      "tieude": tieude,
                                                      "content": content,
                                                      "qas" : qas})
    
    


@app.get("/editData/{id}/{nameCollection}", response_class=HTMLResponse)
def editData(request: Request, id : str, nameCollection: str):
    collection = mydb[nameCollection]
    myquery = {"_id":  ObjectId(id)}
    obj = collection.find_one(myquery)
    content = obj['content']
    qas = obj['qas']
    return templates.TemplateResponse("editData.html", {
        "request": request, 
        "content" : content,
        "qas" : qas,
        "id": id,
        "nameCollection":nameCollection,
    })
    
    

def UpdateProcess(collection, idObj, content, listQuestion , listAnswer):# update m???t b???ng ghi trong db
    listContent = numbering.contentToList(content)
    listQAS = list()
    for i in range(len(listAnswer)):
        answer = listAnswer[i]
        question = listQuestion[i]
        start = numbering.findSentence(answer,listContent)
        objAnswer = ANS(
            text = answer,
            answer_start = start
        )
        id = (uuid.uuid4().hex)
        objQuestionAndAnswer = QAS(
            question = question,
            id = id,
            answer = objAnswer
        )
        listQAS.append(objQuestionAndAnswer.dict())
    print(len(listQAS))
    newData = data(
        content = content,
        qas = listQAS
    )
    myquery = {"_id":  ObjectId(idObj)}
    newvalues = { "$set": newData.dict()}
    
    collection.update(myquery, newvalues)
    return (newData.dict())
    
    
    
    
@app.post('/update-data')
async def updateData(content : str = Form(...), qas : list = Form(...), id = Form(...), nameCollection: str = Form(...)):
    print(id)
    collection = mydb[nameCollection]
    listQuestion = numbering.createListQuestion(qas)
    listAnswer = numbering.createListAnswer(qas)
    return UpdateProcess(collection, id, content, listQuestion, listAnswer)
    
    
    
    
@app.get("/guide", response_class=HTMLResponse)
def write_home(request: Request):
    return templates.TemplateResponse("guide.html", {"request": request})


# ========================================= CRAWL DATA ===========================================================


@app.get("/crawl", response_class=HTMLResponse)
async def form_delete(request: Request):
    colname = mydb.list_collection_names()
    print(colname)
    return templates.TemplateResponse("crawl.html", {"request": request, "CollectionName":colname})

@app.post('/crawl')
async def createCollection(request: Request,nameCollection: str  = Form(...), url: str = Form(...)):
    diclist = crawlData(url)
    collection = mydb[nameCollection]
    for li in diclist:
        content = li['content']
        qas = li['qas']
        listQuestion = numbering.createListQuestion(qas) 
        listAnswer = numbering.createListAnswer(qas)
        MainProcess(collection, content, listQuestion, listAnswer)
    return templates.TemplateResponse("success.html",{"request": request})



def crawlData(url):
    dictList = []
    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')
    news = soup.find_all('div', attrs={'class' : 'para-wrap'})

    for i in range(len(news)):
        content = (news[i].find('pre').text)
        qaswrap = news[i].find_all('div', class_='qa-wrap')
        li = []
        for j in range(len(qaswrap)):
            question = qaswrap[j].find_all('strong',class_='question')
            answer = qaswrap[j].find_all('span',class_='answer')
            if(not len(answer)):
                answer = qaswrap[j].find_all('span',class_='no-answer')
            if(len(question)):
                li.append(question[0].text)
                li.append(answer[0].text)
        temp = NEWS(
            content = content,
            qas = li
        ).dict()
        dictList.append(temp)
        
    return dictList

#================== GG Search ========================

@app.get("/searchGG", response_class=HTMLResponse)
async def Find_Ans(request: Request):
    ListAns = []
    ListLink = []
    leng = 0
    question = ""
    ListRecent = ggapi.recentQuestion()
    return templates.TemplateResponse("SearchGG.html", {"request": request, "ListAns":ListAns, "ListLink":ListLink , "leng":leng , "question" : question, "ListRecent" :ListRecent})

@app.post('/searchGG')
async def Find_Ans(request: Request,question: str  = Form(...)):
    (ListAns,ListLink,content) = ggapi.GGSearchAPI(question)
    leng = (len(ListAns))
    print("S??? k???t qu??? t??m ???????c ===========> ",leng)
    ListRecent = ggapi.recentQuestion()
    return templates.TemplateResponse("SearchGG.html",{"request": request,"ListAns":ListAns, "ListLink":ListLink, "leng":leng, "question" : question , "ListRecent" :ListRecent})



#================== RECORD AUDIO TO VOICE HANDLE ========================

@app.get("/record", response_class=HTMLResponse)
async def record(request: Request):

    return templates.TemplateResponse("record.html", {"request": request})



@app.post('/receive')
async def receiveData(request: Request,file: UploadFile= File(...)):
    print(file.filename)
    audio_bytes = file.file.read()
    
    with open("audio.wav","wb") as f: 
        f.write(audio_bytes)

    return templates.TemplateResponse("record.html",{"request": request})

