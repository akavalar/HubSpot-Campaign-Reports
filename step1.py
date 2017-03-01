#uses only base Python 2.7 modules, i.e. does not use any external modules like pandas or requests
import sys, time, csv, os, json, urllib2


#get all campaign IDs, names and subjects from Hubspot using the API key and save the output to a text file
def get_Hubspot_campaign_names_and_IDs(hapikey):
    #output filename
    timestamp = str(int(time.time()))
    results = 'Hubspot_campaign_names_and_IDs_{0}.txt'.format(timestamp)
    
    #output path
    folder_child = "Hubspot Reports ({0})".format(timestamp)    
    os.mkdir(folder_child)
    os.chdir(folder_child)
    target = os.path.join(os.getcwd(), results)
    
    #URL - get all campaigns: developers.hubspot.com/docs/methods/email/get_campaigns_by_id
    url_all_campaigns = 'https://api.hubapi.com/email/public/v1/campaigns/by-id?hapikey={0}&limit=1000'
    #URL - get data for each campaign: developers.hubspot.com/docs/methods/email/get_campaign_data
    url_campaign_data = 'https://api.hubapi.com/email/public/v1/campaigns/{0}?appId={1}&hapikey={2}'
    
    #get all campaigns   
    response = urllib2.urlopen(url_all_campaigns.format(hapikey))
    response = json.load(response)[u'campaigns']       
    
    #ignore "Workflow" campaigns
    campaigns = [[row[u'appId'], row[u'id']] for row in response if row[u'appName'] != 'Workflow']
    
    #get data for each campaign
    output = []
    num = len(campaigns)
    for campaign in range(num):
        print('Requesting campaign name and subject for campaign {0} out of {1}'.format((campaign+1), num))
        
        #retrieve names and subjects of campaigns
        appID = campaigns[campaign][0]
        campaignID = campaigns[campaign][1]
        response = urllib2.urlopen(url_campaign_data.format(campaignID, appID, hapikey))
        response = json.load(response)
        
        #construct rows of the output file
        output.append([response[u'name'], response[u'subject'], campaignID, appID])
    
    #add header    
    output_header = [["Name", "Subject", "Email Campaign ID", "Email Campaign Type ID"]]
    output_header.extend(output)
 
    #save output file
    with open(target, 'wb') as f:
        writer = csv.writer(f, delimiter='|', quoting=csv.QUOTE_NONNUMERIC)
        writer.writerows(output_header)
    

folder = sys.argv[1]    
APIkey = sys.argv[2]


if __name__ == '__main__':
    #set working directory
    os.chdir(folder)
    
    #get all campaign IDs, names and subjects from Hubspot using the API key and save the output to a text file
    get_Hubspot_campaign_names_and_IDs(APIkey)