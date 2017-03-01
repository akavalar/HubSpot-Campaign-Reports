#uses only base Python 2.7 modules, i.e. does not use any external modules like pandas or requests
import sys, urllib2, time, csv, os, imaplib, shutil, zipfile, json, cookielib


#wrapper for simple POST requests using data, headers and parameters (inside the URL), no cookies
def request_post(url, headers, data):
    req = urllib2.Request(url) #parameters are inside the URL
    #add JSON data
    req.add_data(data)
    #add headers
    for header in headers:
        req.add_header(header, str(headers[header]))
    #POST request
    response = urllib2.urlopen(req)
    return response
    

#wrapper for POST requests using cookies, data, headers, params - initialize session
def session_init():
    cookies = cookielib.CookieJar()
    session = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))
    return session


#wrapper for POST requests using cookies, data, headers, params - continue session
def session_post(session, url, headers, data):
    req = urllib2.Request(url)
    #add JSON data
    req.add_data(data)
    #add headers
    for header in headers:
        req.add_header(header, str(headers[header]))
    #POST request
    response = session.open(req)
    return response 
    

#get access token required for authentication (API key does *not* work here!)
def get_token(user_hubspot, pwd_hubspot):
    session = session_init()
    portalID = 9999999
    
    headers1 = {
        'Origin': 'https://app.hubspot.com',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.8,sl;q=0.6,de;q=0.4,es;q=0.2,hr;q=0.2',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        'Referer': 'https://app.hubspot.com/login/',
        'Connection': 'keep-alive',
        'Accept': '*/*',
        'Host': 'app.hubspot.com',
        'Content-Type': 'application/json',
        'Content-Length': '',
        'X-Requested-With': 'XMLHttpRequest',
        'DNT': '1'
        }
    data1 = '{{"email":"{0}","password":"{1}","rememberLogin":false}}'.format(user_hubspot, pwd_hubspot)
    headers1["Content-Length"]=str(len(data1))
    url1 = 'https://app.hubspot.com/login-api/v1/login'
    response1 = session_post(session, url1, headers1, data1)

    headers2 = {
        'Origin': 'https://app.hubspot.com',
        'Accept-Encoding': 'deflate, br', #remove "gzip" otherwise you get gzipped content (urllib2 can't handle it)
        'Accept-Language': 'en-US,en;q=0.8,sl;q=0.6,de;q=0.4,es;q=0.2,hr;q=0.2',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36',
        'Content-type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'Referer': 'https://app.hubspot.com/login/',
        'Connection': 'keep-alive',
        'DNT': '1'
        }
    data2 = 'portalId={0}'.format(portalID)
    url2='https://app.hubspot.com/login-verify'
    response2 = session_post(session, url2, headers2, data2)

    token = str(json.loads(response2.read())["auth"]["access_token"]["token"])

    #done    
    print("\nAccess token successfully retrieved.\n")
    return token
    

#connect to the GMail server and preemptively clean up the inbox
#make sure access for less secure apps enabled: https://www.google.com/settings/security/lesssecureapps
def clean_up_gmail(pwd_gmail):
    
    #enter GMail password (masked)
    user_gmail = "your_email_address@gmail.com"
    #pwd_gmail = getpass.getpass("Enter password for your_email_address@gmail.com: ")
    
    #connect to the GMail server using supplied credentials
    gmail = imaplib.IMAP4_SSL("imap.gmail.com")
    gmail.login(user_gmail, pwd_gmail)

    gmail.select("HubSpot Reports")
        
    #look for unread emails
    response, items = gmail.search(None, "ALL")
    
    #get the email IDs
    items = items[0].split()

    #get file URLs        
    for item in items:
        
        #mark email as seen (will not process it in the next iteration)
        gmail.store(item, '+FLAGS', '\Seen')
        
    #close out of the mailbox
    gmail.close()
        
    #logout
    gmail.logout()
    
    print("\nAll old emails marked as read.")
    

#request that basic campaign stats be sent to the chosen GMail address for all campaigns found in the file
def request_campaign_data_basic(target, access_token):
    #read in data from file
    with open(target) as f:
        campaigns = [row[0].split('|') for row in csv.reader(f) if row!=[]]
        #remove header
        campaigns = campaigns[1:len(campaigns)]

    #setup (basic)
    email = "your_email_address@gmail.com"
    portalID = 9999999
    headers_basic = {
        'Origin': 'https://app.hubspot.com',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Host': 'api.hubapi.com',
        'Content-Type': 'application/json',
        'Content-Length': ''
        }
    data_basic = '{{"emailCampaignIds":[{0}],"includedEventTypes":["SENT","DELIVERED","OPEN","CLICK","UNSUBSCRIBED","SPAMREPORT","BOUNCE","DEFERRED","MTA_DROPPED","DROPPED"],"excludedEventTypes":[],"events":["PROCESSED","DELIVERED","OPEN","CLICK","UNSUBSCRIBED","SPAMREPORT","DEFERRED","BOUNCE","DROPPED"],"email":"{1}","portalId":{2}}}'
    url_basic = 'https://api.hubapi.com/email/v1/export?access_token={0}&portalId={1}'

    #request campaign data
    num = len(campaigns)
    num_successful = 0
    for campaign in range(num):
        campaignID=campaigns[campaign][2]
        print('Requesting basic data for campaign {0} ({1}) out of {2}'.format((campaign+1), campaignID, num))
        
        #basic request
        data = data_basic.format(campaignID, email, portalID)
        headers_basic["Content-Length"] = str(len(data))        
        request = request_post(url_basic.format(access_token, portalID), headers_basic, data)          

        if request.code == 200 or request.code == 204 :
            print("Successfully requested. Data will be sent to {0}.".format(email))
            num_successful+=1
        else:
            print("Problem encountered (skipped).")

        #just in case
        time.sleep(2)
    
    #done
    print("\nProcessed all campaigns.\n")
    return num_successful
    

#request that advanced campaign stats be sent to the chosen GMail address for all campaigns found in the file
def request_campaign_data_advanced(target, access_token):
    #read in data from file
    with open(target) as f:
        campaigns = [row[0].split('|') for row in csv.reader(f) if row!=[]]
        #remove header
        campaigns = campaigns[1:len(campaigns)]

    #setup (advanced)
    email = "your_email_address@gmail.com"
    portalID = 9999999
    headers_advanced = {
        'Origin': 'https://app.hubspot.com',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept-Language': 'en-US,en;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Host': 'api.hubapi.com',
        'Content-Type': 'application/json',
        'Content-Length': ''
        }
    data_advanced = '{{"format":"csv","email":"{0}","appCampaignIds":[{{"appId":{1},"emailCampaignId":{2}}}],"eventTypes":["SENT","DROPPED","DELIVERED","BOUNCE","DEFERRED","OPEN","CLICK","UNSUBSCRIBED","SPAMREPORT"],"portalId":{3}}}'
    url_advanced = 'https://api.hubapi.com/email/v1/export-events/campaign?access_token={0}&portalId={1}'

    #request campaign data
    num = len(campaigns)
    num_successful = 0
    for campaign in range(num):
        campaignID=campaigns[campaign][2]      
        appID=campaigns[campaign][3]
        print('Requesting advanced data for campaign {0} ({1}) out of {2}'.format((campaign+1), campaignID, num))

        #advanced request
        data = data_advanced.format(email, appID, campaignID, portalID)
        headers_advanced["Content-Length"] = str(len(data))
        request = request_post(url_advanced.format(access_token, portalID), headers_advanced, data)
        
        if request.code == 200 or request.code == 204: #for some reason, the status code here is not 200, but 204
            print("Successfully requested. Data will be sent to {0}.".format(email))
            num_successful+=1
        else:
            print("Problem encountered (skipped).")
        
        #just in case
        time.sleep(2)
    
    #done
    print("\nProcessed all campaigns.\n")
    return num_successful
    

#connect to the GMail server and collects all attachment links
#make sure access for less secure apps enabled: https://www.google.com/settings/security/lesssecureapps
def get_attachment_links(pwd_gmail, num_successful):
    #wait 30 seconds
    print("Wait 15 seconds before attempting to fetch data from GMail.\n")
    time.sleep(15)
    
    #enter GMail password (masked)
    user_gmail = "your_email_address@gmail.com"
    #pwd_gmail = getpass.getpass("Enter password for your_email_address@gmail.com: ")
    
    #connect to the GMail server using supplied credentials
    gmail = imaplib.IMAP4_SSL("imap.gmail.com")
    gmail.login(user_gmail, pwd_gmail)

    #instantiate the attachments list to be populated with file URLs
    attachments = []

    #instantiate counter for while loop
    num_emails = 0
    
    #retrieve unread emails, parse the URL of the file, mark as read
    while num_emails < num_successful:
        print("So far processed {0} emails out of {1}.".format(num_emails, num_successful)) 
        
        #select mailbox
        gmail.select("HubSpot Reports")
        
        #look for unread emails
        response, items = gmail.search(None, "UNSEEN")
        
        #get the email IDs
        items = items[0].split()

        #get file URLs        
        for item in items:            
            #fetch entire email
            response, data = gmail.fetch(item, "(RFC822)")
            
            #get email body, manipulate a bit to account for line wrapping
            email_body = data[0][1]
            email_body = email_body.replace("\r\n", "").replace("=3D", "|").replace("=", "").replace("|", "=")

            #get the URL
            link = email_body.split("Download my data")[1].split("href=\"")[1].split("\"")[0]
            attachments.append(link)
            
            #mark email as seen (will not process it in the next iteration)
            gmail.store(item, '+FLAGS', '\Seen')
            
        #close out of the mailbox
        gmail.close()
        
        #get unique URLs to prevent double-counting
        attachments=list(set(attachments))
        
        #update num_emails
        num_emails=len(attachments)
        
        #wait 2s
        time.sleep(2)
        
    #logout
    gmail.logout()
    
    #return collected links
    print("\nDone processing all emails.")
    return attachments


#download all collected attachment links
def download_files(attachments):
    for attachment in attachments:
        filename = attachment.split("?")[0].split('/')[-1]
        
        #request stats
        req = urllib2.urlopen(attachment)
            
        #save downloaded file
        with open(filename, 'wb') as f:
            shutil.copyfileobj(req, f)

    print("\nAll files downloaded.")


#extract all archive files, rename each file based on the respective archive, delete archive files
def extract_files(folder):
    for content in os.listdir(folder):
        if content.endswith(".zip"):
            archive=zipfile.ZipFile(content)
            for member in archive.namelist(): #just one member, but still...
                archive.extract(member)
                source = file(os.path.join(folder, member))
                target = os.path.splitext(os.path.basename(content))[0]+".csv"
                target = file(os.path.join(folder, target), 'wb')
                shutil.copyfileobj(source, target)
                source.close()
                target.close()
                os.remove(source.name)
            archive.close()
            os.remove(content)
    print("\nAll files extracted.")
    
    
#read in individual CSV files, concatenate them and output results
def merge_files(folder):
    #read in individual files and concatenate them, create a list of lists (i.e. list of rows)
    results = []
    results_header = []
    for item in os.listdir(folder):
        if item.endswith(".csv"):
            with open(os.path.join(folder,item)) as f:
                contents = [row for row in csv.reader(f)]
             
                if (results_header == []):
                     results_header = [contents[0]]
                contents = contents[1:len(contents)] # drop first row
                
                for record in contents:
                    results.append(record)
    
    results_header.extend(results)
    
    #locate and read in crosswalk with names and subjects    
    for item in os.listdir(folder):
        if item.startswith("Hubspot_campaign_names_and_IDs_"):
            with open(os.path.join(folder,item)) as f:
                contents = [row for row in csv.reader(f, delimiter='|') if row!=[]]
     
            index_contents_name = contents[0].index("Name") #position in crosswalk list
            index_contents_id = contents[0].index("Email Campaign ID") #position in crosswalk list
            
            crosswalk = []
            for item in contents:
                crosswalk.append(list(item[i] for i in [index_contents_name, index_contents_id])) #subset 2 columns by their names
    
    #merge two arrays by "Email Campaign ID"
    index_results = results_header[0].index("Email Campaign ID") #position in results_header list
    index_cross = crosswalk[0].index("Email Campaign ID") #position in crosswalk list (can't reuse from above)
    
    for i in range(1,len(crosswalk)):
        for j in range(1,len(results_header)):
            if results_header[j][index_results] == crosswalk[i][index_cross]:
                results_header[j].append(crosswalk[i][0])
    results_header[0].append("Email Campaign Name")
    
    #output results
    with open(os.path.join(folder,'Results_basic.csv'), 'wb') as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        for row in results_header:
            writer.writerow(row)
    
    print("\nAll files successfully merged. Output written to Results_basic.csv file.\n")


folder = os.path.dirname(os.path.abspath(sys.argv[1]))
results = sys.argv[1]
user_hubspot = sys.argv[2]
pwd_hubspot = sys.argv[3]
pwd_gmail = sys.argv[4]


if __name__ == '__main__':
    #set working directory
    os.chdir(folder)

    #clean up GMail
    clean_up_gmail(pwd_gmail)
    
    #get access_token
    access_token = get_token(user_hubspot, pwd_hubspot)
    
    #request that basic/advanced campaign stats be sent to the chosen GMail address for all campaigns found in the file
    num_files = request_campaign_data_basic(results, access_token)
    
    #connect to the GMail server and collects all attachment links
    attachments = get_attachment_links(pwd_gmail, num_files)
        
    #download all collected attachment files
    download_files(attachments)
    
    #extract files from archives
    extract_files(folder)
    
    #read in individual CSV files, concatenate them and output results
    merge_files(folder)