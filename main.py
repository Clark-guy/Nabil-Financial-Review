import imaplib
import email
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pickle
import os
from datetime import datetime, timedelta
#import getpass
#from email.header import decode_header
from bs4 import BeautifulSoup




def getDatesAndBalances():

    # Define credentials
    try:
        username = os.environ["GMAIL_USERNAMEE"]
        password = os.environ["GMAIL_APP_PASSWORD"]
    except:
        username = input("Enter your username: ")
        password = input("Enter your app password: ")

    # Connect to Gmail IMAP server
    mail =imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, password)
    mail.select("inbox")

    # Search for all emails
    status, messages = mail.search(
        None, 
        "FROM 'txn-alert@nabilbank.com'"
        )

    email_ids = messages[0].split()
    balances = []
    for e_id in email_ids:
        res, msg_data = mail.fetch(e_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                print(msg["FROM"]+ ' - ' +msg["SUBJECT"]+ ' - ' +msg["DATE"])
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        body = part.get_payload(decode=True).decode()
                        soup = BeautifulSoup(body, "html.parser")
                        table = soup.find_all("table")[3]
                        rows = table.find_all("tr")
                        #headers = rows[0].find_all("td")
                        cells = rows[1].find_all("td")
                        i = tuple((cells[0].get_text(strip=True), cells[3].get_text(strip=True)))
                        balances.append(i)
    mail.logout()
    return balances


def saveBalances(balances: list[tuple], filename: str):
    with open(filename, 'wb') as f:
        pickle.dump(balances, f)

def loadBalances(filename: str):
    with open(filename, 'rb') as f:
        return pickle.load(f)

def deDuplicateBalances(balances: list[tuple]):
    #convert all first items in list to date
    inputDateFormat = "%Y-%m-%d %H:%M"
    dateBalances = [tuple((datetime.strptime(balance[0], inputDateFormat).date(), balance[1])) for balance in balances]
    # remove all duplicate dates leaving the LAST balance for each day
    i = 0
    while i < len(dateBalances)-1:
        if i+1 < len(dateBalances):
            if dateBalances[i+1][0] == dateBalances[i][0]:
                dateBalances.remove(dateBalances[i])
            else:
                i+=1

    outputBalances = [tuple((balance[0].strftime('%Y-%m-%d')[-5:], balance[1])) for balance in dateBalances] #setting back to strings
    return dateBalances #outputBalances 
    


#walk through all indexes of range
#if the next index represents the next day, append current index and increase index by 1
#if not, append the next day, SAME value, do not increase index
def fillDateGaps(balances: list[tuple]):
    newBalances = []
    startDate = balances[0][0]
    endDate = balances[len(balances)-1][0]
    i = 0
    daysAddedCounter = 1
    while i <= len(balances)-2:
        if i+1 < len(balances):
            #if the next day from balances is the same day as today plus 1
            if balances[i+1][0] == balances[i][0]+timedelta(days=daysAddedCounter):
                newBalances.append(tuple((balances[i+1][0], balances[i][1])))
                daysAddedCounter = 1
                i+=1
            else:
                newBalances.append(tuple((balances[i][0]+timedelta(days=daysAddedCounter), balances[i][1])))
                daysAddedCounter+=1
    return newBalances

    


def main():

    #couple o vars
    filename = "balances.pkl"
    font = {'family': 'cursive',
            'color':  'darkred',
            'weight': 0,
            'size': 16,
            }


    try:
        print(f"Trying to load balances from file: {filename}")
        balances = loadBalances(filename)
    except FileNotFoundError:
        print(f"File not found! Attempting to load from IMAP")
        balances = getDatesAndBalances()
        saveBalances(balances, filename)
    except Exception as e:
        print(f"Error occurred: {e}")
    
    #balances = getDatesAndBalances()
    #saveBalances(balances)
    #balances = loadBalances()
    balances = deDuplicateBalances(balances)
    balances = fillDateGaps(balances)


    #convert balances to independent date and rupee variables for plotting
    dates = [(x[0]) for x in balances]
    rupees = [float(y[1].replace(',','')) for y in balances]

    plt.plot(dates, rupees)
    #plt.xticks(rotation=-40, ha='left', rotation_mode='anchor')#, fontsize=6)
    plt.tick_params(axis='x', direction='in', length=6)
    plt.subplots_adjust(bottom=.22)
    plt.title("James' Financial Ruin, Visualized", fontdict=font)
    plt.ylabel("Purchasing Power (NPR)", fontdict=font)
    fig, ax = plt.gcf(), plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 5, 10, 15, 20, 25]))
    sec = ax.secondary_xaxis(location=-0.075)
    sec.xaxis.set_major_locator(mdates.MonthLocator(bymonthday=1))
    sec.xaxis.set_major_formatter(mdates.DateFormatter('  %b'))
    sec.tick_params('x', length=0)
    sec.spines['bottom'].set_linewidth(0)
    sec.set_xlabel("Date", fontdict=font)
    plt.show()



if __name__ == "__main__":
    main()