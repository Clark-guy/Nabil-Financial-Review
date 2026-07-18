import imaplib
import email
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pickle
import os
from datetime import datetime, timedelta
#from email.header import decode_header
from bs4 import BeautifulSoup



# Define credentials

username = os.environ["GMAIL_USERNAME"]
password = os.environ["GMAIL_APP_PASSWORD"]

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


font = {'family': 'cursive',
        'color':  'darkred',
        'weight': 0,
        'size': 16,
        }




def getDatesAndBalances():
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
    return balances


def saveBalances(balances: list[tuple]):
    with open('balances.pkl', 'wb') as f:
        pickle.dump(balances, f)

def loadBalances():
    with open('balances.pkl', 'rb') as f:
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

    





#balances = getDatesAndBalances()
#saveBalances(balances)
balances = loadBalances()
balances = deDuplicateBalances(balances)
balances = fillDateGaps(balances)


#print(balances[0])
#for b in balances:
#    print(b)

x_val = [(x[0]) for x in balances]
y_val = [float(y[1].replace(',','')) for y in balances]

plt.plot(x_val, y_val)

#comment these two lines out to see just months
#plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

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


#plt.subplots_adjust(left=.1)
#plt.subplots_adjust(right=2)
plt.show()


#how im doing this now, it will pull every email, thus resulting in an uneven spread on the x axis of dates.
#e.g., say i buy 1 thing on tuesday, then 4 things on wednesday, then 1 thing on thursday
#i will have 6 data points, which will be somewhat hard to read - it will look like its spread across 6 days
#solutions
# - I could just grab one email per day, the most recent one
#   - this ignores if i was out late one night and then ended up buying more shit
#   - probably not worth nitpicking that much
# - I could color points based on the day - even day black point, odd day grey 
#   - this saves me from having to go crazy rewriting anything, and also gives a more complete chart

mail.logout()
