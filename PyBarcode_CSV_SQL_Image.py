from pyzbar import pyzbar
import argparse
import cv2
import numpy as np
import pandas as pd
import datetime
import os
import sqlite3
import wget

def dir_check(folder_name):
    if(os.path.isdir(folder_name)):
        return
    else:
        os.mkdir(folder_name)
        return   

def updating_csv(output_folder_name,barcodedict,file_name="default creation/backup"):
    print("Updating CSV with "+file_name)
    
    dir_check(output_folder_name)
    
    new_df=pd.DataFrame(list(barcodedict.items()),columns=["Barcode","Datetime_of_Entering"])
    new_df.to_csv(output_folder_name+"/Barcode_CSV.csv",index=False)
    

def updating_sql(conn,cur,new_barcodeDict,file_name="default creation/backup"):
    print("Updating SQL with "+file_name)
    
    cur.execute('''DELETE FROM Barcodes''')
    
    for barcode,datetime in new_barcodeDict.items():
        cur.execute('''INSERT OR IGNORE INTO Barcodes (Barcode,Datetime_of_Entering)VALUES ( ?,? )''',(barcode,datetime,))
    conn.commit()   
    
def confirmation_and_entering_barcodes(img):
    print("Waiting for confirmation")
    
    cv2.namedWindow("Confirmation Window")
    cv2.imshow("Confirmation Window",img)
    if cv2.waitKey(0) & 0xFF==ord("s"):
        print("Selected")
        cv2.destroyWindow("Confirmation Window")
        return True
    elif cv2.waitKey(0) & 0xFF==ord("d"):
        print("Not Selected")
        cv2.destroyWindow("Confirmation Window")
        return False

def update(conn,cur,barcodedict,output_folder_name,file_name):
    updating_csv(output_folder_name,barcodedict,file_name)
    updating_sql(conn,cur,barcodedict,file_name)   
    
def checking_barcodes(conn,cur,barcodes,file_name,barcodedict,barcode_folder_name,barcode_marked_folder_name,output_folder_name):
    print("Checking Barcodes for "+file_name)
    
    for barcode in barcodes:
        barcodeData=barcode.data.decode("utf-8")
        if(barcodeData in barcodedict):
            continue
        else:
            timing=datetime.datetime.now()
            barcodedict[barcodeData]=timing
    
    update(conn,cur,barcodedict,output_folder_name,file_name)
    
def create_barcode_marked_images(conn,cur,img,barcodes,file_name,barcodedict,barcode_folder_name,barcode_marked_folder_name,output_folder_name):
    print("Creating Barcode Marked Images for "+file_name)
    
    img1=img.copy()
    if(len(barcodes)<1):
        return
    else:
        for barcode in barcodes:
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

            barcodeData=barcode.data.decode("utf-8")
            barcodeType=barcode.type

            text = "{} ({})".format(barcodeData, barcodeType)
            cv2.putText(img, text, (x, y - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
        dir_check(barcode_marked_folder_name)
        
        if(confirmation_and_entering_barcodes(img)):
            print("Confirmed")
            cv2.imwrite(barcode_folder_name+"/"+file_name,img1)
            cv2.imwrite(barcode_marked_folder_name+"/"+file_name,img)
            checking_barcodes(conn,cur,barcodes,file_name,barcodedict,barcode_folder_name,barcode_marked_folder_name,output_folder_name)
            return
        else:
            print("Deleted")
            return 
    
def check_barcodedict(barcodedict,barcodes):
    new_barcodes=list()
    for barcode in barcodes:
        if(barcode.data.decode("utf-8") in barcodedict):
            continue
        else:
            new_barcodes.append(barcode)
    return new_barcodes

def cleanslate_protocol(barcode_folder_name,barcode_marked_folder_name,output_folder_name):
    print("Clean Slate Protocol")
    
    if(os.path.isdir(barcode_folder_name)):
        if(len(os.listdir(barcode_folder_name+"/"))>0):
            pass
        else:
            os.rmdir(barcode_folder_name+"/")
    else:
        pass
    
    if(os.path.isdir(barcode_marked_folder_name)):
        if(len(os.listdir(barcode_marked_folder_name+"/"))>0):
            pass
        else:
            os.rmdir(barcode_marked_folder_name+"/")
    else:
        pass
    
    if(os.path.isdir(output_folder_name)):
        if(len(os.listdir(output_folder_name+"/"))>0):
            for file_name in os.listdir(output_folder_name+"/"):
                if(str(file_name).endswith(".sqlite")):
                    conn=sqlite3.connect(output_folder_name+"/"+file_name)
                    cur=conn.cursor()
                    try:
                        cur.execute('''SELECT * FROM Barcodes''')
                        rows=cur.fetchall()
                        if(len(rows)>1):
                            pass
                        else:
                            os.remove(output_folder_name+"/"+file_name)
                    except Exception as e:
                        print(e)
                        pass
                elif(str(file_name).endswith(".csv")):
                    df=pd.read_csv(output_folder_name+"/"+file_name)
                    if(df.empty):
                        os.remove(output_folder_name+"/"+file_name)
                    else:
                        pass
                if(len(os.listdir(output_folder_name+"/"))>0):
                    pass
                else:
                    os.rmdir(output_folder_name+"/")
        else:
            os.rmdir(output_folder_name+"/")
    else:
        pass    
    
    return

def download_barcodes(barcode_folder_name):
    print("Downloading")
    urls=["http://free-barcode.com/howto/images/1Dbarcode2Dbarcode01.PNG",
          "https://smtnet.com/media/images/Microscan-Multiple-Barcodes.jpg",
          "https://cdn3.vectorstock.com/i/1000x1000/00/97/set-of-different-barcodes-isolated-on-white-vector-17020097.jpg",
          "https://images.onlinelabels.com/images/learning-center/articles/nine_barcode_types.png"]
    for url in urls:
        file=wget.download(url,barcode_folder_name)

def backup(csv_file_name,sql_file_name,barcodedict,backup_folder_name):
    print("Backing Up")
    
    dir_check(backup_folder_name)
    
    try:
        if(os.path.exists(backup_folder_name+"/"+csv_file_name) and os.path.exists(backup_folder_name+"/"+sql_file_name)):
            print("Both")
            barcodedict=retrieve_csv_data(csv_file_name,barcodedict,backup_folder_name)
            conn,cur,barcodedict=initialize_db(sql_file_name,barcodedict,backup_folder_name)
            update(conn,cur,barcodedict,backup_folder_name,"backing_up")
        elif(os.path.exists(backup_folder_name+"/"+csv_file_name) or os.path.exists(backup_folder_name+"/"+sql_file_name)):
            if(os.path.exists(backup_folder_name+"/"+csv_file_name)):
                print("CSV")
                barcodedict=retrieve_csv_data(csv_file_name,barcodedict,backup_folder_name)
                conn,cur,barcodedict=initialize_db(sql_file_name,barcodedict,backup_folder_name)
                update(conn,cur,barcodedict,backup_folder_name,"backing_up")
            else:
                print("SQL")
                conn,cur,barcodedict=initialize_db(sql_file_name,barcodedict,backup_folder_name)
                update(conn,cur,barcodedict,backup_folder_name,"backing_up")
        else:
            print("Both No")
            dir_check(backup_folder_name)
            conn,cur,barcodedict=initialize_db(sql_file_name,barcodedict,backup_folder_name)
            update(conn,cur,barcodedict,backup_folder_name,"backing_up")
    except Exception as e:
        print(e)


def execute(conn,cur,barcodedict,barcode_folder_name,barcode_marked_folder_name,output_folder_name,backup_folder_name):
    print("Executing")
    
    dir_check(barcode_folder_name)
    
    if(len(os.listdir(barcode_folder_name+"/"))>0):
        for file_name in os.listdir(barcode_folder_name+"/"):
            if(str(file_name).lower().endswith(".png") or str(file_name).lower().endswith(".jpg")):
                img=cv2.imread(barcode_folder_name+"/"+file_name)
                barcodes=pyzbar.decode(img)
                barcodes=check_barcodedict(barcodedict,barcodes)
                if(len(barcodes)<1):
                    continue
                else:
                    create_barcode_marked_images(conn,cur,img,barcodes,file_name,barcodedict,barcode_folder_name,barcode_marked_folder_name,output_folder_name)
        backup("Barcode_CSV.csv","Barcode_SQL.sqlite",barcodedict,backup_folder_name)
        cleanslate_protocol(barcode_folder_name,barcode_marked_folder_name,output_folder_name)
        cv2.destroyAllWindows()
    else:
        download_barcodes(barcode_folder_name)
        execute(conn,cur,barcodedict,barcode_folder_name,barcode_marked_folder_name,output_folder_name,backup_folder_name)

    
def retrieve_sql_data(rows,barcodedict):
    print("Retrieving SQL Data")
    
    for row in rows:
        if row[0] in barcodedict:
            continue
        else:
            barcodedict[row[0]]=datetime.datetime.strptime(row[1],"%Y-%m-%d %H:%M:%S.%f")

    return barcodedict
    
def initialize_db(sql_file_name,barcodedict,output_folder_name):
    print("Initializing DB")
    
    conn=sqlite3.connect(output_folder_name+"/"+sql_file_name)
    cur=conn.cursor()
    try:
        cur.execute('SELECT * FROM Barcodes')
        rows=cur.fetchall()
        barcodedict=retrieve_sql_data(rows,barcodedict)
        return (conn,cur,barcodedict)
    except Exception as e:
        print("Creating Table")
        cur.execute('''CREATE TABLE IF NOT EXISTS Barcodes (Barcode TEXT,Datetime_of_Entering TIMESTAMP)''')
        return(conn,cur,barcodedict)

def retrieve_csv_data(csv_file_name,barcodedict,output_folder_name):
    print("Retrieving CSV Data")
    try:
        old_df=pd.read_csv(output_folder_name+"/"+csv_file_name)
        temp_barcodedict=old_df.set_index("Barcode").T.to_dict("list")
        for key,value in temp_barcodedict.items():
            if key in barcodedict:
                continue
            else:
                barcodedict[key]=datetime.datetime.strptime(value[0],"%Y-%m-%d %H:%M:%S.%f")
        return barcodedict
    except Exception as e:
        print(e)
        return barcodedict 

def retrieve_backup_data(csv_file_name,sql_file_name,backup_folder_name):
    print("Retrieving Backup Data")
    barcodedict=dict()
    dir_check(backup_folder_name)
    if(csv_file_name in os.listdir(backup_folder_name+"/")):
        barcodedict=retrieve_csv_data(csv_file_name,barcodedict,backup_folder_name)
    if(sql_file_name in os.listdir(backup_folder_name+"/")):
        conn,cur,barcodedict=initialize_db(sql_file_name,barcodedict,backup_folder_name)
    return barcodedict
    
def initialization(csv_file_name,sql_file_name,barcode_folder_name,barcode_marked_folder_name,output_folder_name,backup_folder_name):
    print("Initializing")
    
    try:
        if(os.path.exists(output_folder_name+"/"+csv_file_name) and os.path.exists(output_folder_name+"/"+sql_file_name)):
            print("Both CSV and SQL files available")
            barcodedict=retrieve_backup_data(csv_file_name,sql_file_name,backup_folder_name)
            barcodedict=retrieve_csv_data(csv_file_name,barcodedict,output_folder_name)
            conn,cur,barcodedict=initialize_db(sql_file_name,barcodedict,output_folder_name)
            execute(conn,cur,barcodedict,barcode_folder_name,barcode_marked_folder_name,output_folder_name,backup_folder_name)
        elif(os.path.exists(output_folder_name+"/"+csv_file_name) or os.path.exists(output_folder_name+"/"+sql_file_name)):
            if(os.path.exists(output_folder_name+"/"+csv_file_name)):
                print("Only CSV file available")
                barcodedict=retrieve_backup_data(csv_file_name,sql_file_name,backup_folder_name)
                barcodedict=retrieve_csv_data(csv_file_name,barcodedict,output_folder_name)
                conn,cur,barcodedict=initialize_db(sql_file_name,barcodedict,output_folder_name)
                updating_sql(conn,cur,barcodedict)
                execute(conn,cur,barcodedict,barcode_folder_name,barcode_marked_folder_name,output_folder_name,backup_folder_name)
            else:
                print("Only SQL file available")
                barcodedict=retrieve_backup_data(csv_file_name,sql_file_name,backup_folder_name)
                conn,cur,barcodedict=initialize_db(sql_file_name,barcodedict,output_folder_name)
                updating_csv(output_folder_name,barcodedict)
                execute(conn,cur,barcodedict,barcode_folder_name,barcode_marked_folder_name,output_folder_name,backup_folder_name)
        else:
            print("Both CSV and SQL not available")
            dir_check(output_folder_name)
            barcodedict=retrieve_backup_data(csv_file_name,sql_file_name,backup_folder_name)
            conn,cur,barcodedict=initialize_db(sql_file_name,barcodedict,output_folder_name)
            execute(conn,cur,barcodedict,barcode_folder_name,barcode_marked_folder_name,output_folder_name,backup_folder_name)
    except Exception as e:
        print(e)
        
if __name__=="__main__":
    initialization("Barcode_CSV.csv","Barcode_SQL.sqlite","Barcode_Images","Barcode_Marked_Images","Output_Folder","Backup_Folder")