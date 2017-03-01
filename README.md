# Automate retrieving (and combining) HubSpot campaign reports using Python

HubSpot's API doesn't support accessing detailed campaign reports, so I had to come up with a hack that automates the retrieval (and conmbining) of data associated with each campaign.

## Notes (i.e. make sure you read this)

Note that this is super hacky, super unsupported and might stop working at any time! Also, these scripts are all meant to be called by the Automator app on macOS, which deals with the GUI aspect of supplying the required parameters (choosing paths, entering username, password, API key, email address, etc.), so you might need to modify them a bit here and there. Since this was meant as an internal tool only, there was never any need for concealing the credentials passed to the Python script - you might want to fix that. Also, you'll notice that there's a couple of hardcoded parameters that I never thought I'd turn into arguments of the respective functions since I knew they'll never change. At the very least you'll want to change the email address and the portail ID (`user_gmail` string and `portalID` int), and potentially also the mailbox name (currently "HubSpot Reports"). Note that this code was implemented using a Gmail email address - you should probably just get a new throwaway Gmail email address to keep things simple (and to not clutter your current Gmail inbox, if any). Finally, note that there's absolutely no error catching, etc. - you'll have to debug and fix any problems you might encounter.

## Rough sketch of the idea

You first retrieve all campaign characteristics (names, IDs, etc.) using HubSpot's API key. Once all this is written to a file, you must manually edit that output file to exclude all those campaigns you're not interested in (i.e. just go and delete those lines). Finally, you need to run the second script (either the version that requests basic or advanced reports - I'm not even sure why I ended up with two almost-identical scripts...) on that edited file as its input. There are other inputs the script will need - see above and check the source code. This second script will connect to your Gmail account and preemptively mark all existing emails as read, then log in to HubSpot to get your "token" that will allow the code to programmatically request reports for all campaigns found in the input file generated in step 1. Since report data can't be downloaded directly but are sent to the email address you've chosen beforehand, the script will then repeatedly check that email address for new, unread emails. Every such email contains a download link that is then parsed from the email body. Once all "attachments" are downloaded, the code will extract the contents of each ZIP file and merge the individual CSV files into one large CSV file (adding columns that will help you keep track of which rows are associated with which campaign).

So basically, the workflow of both scripts looks something like this:

    0. set working directory
    1. get all campaign IDs, names and subjects from Hubspot using the API key and save the output to a text file: `get_Hubspot_campaign_names_and_IDs(APIkey)`
    2. manually remove all campaigns (lines) you don't want to see in your final CSV file
    3. clean up GMail: `clean_up_gmail(pwd_gmail)`
    4. get access_token: `get_token(user_hubspot, pwd_hubspot)`
    5. request that basic/advanced campaign stats be sent to the chosen GMail address for all campaigns found in the file: `request_campaign_data_basic(results, access_token)`
    6. connect to the GMail server and collects all attachment links: `get_attachment_links(pwd_gmail, num_files)`
    7. download all collected attachment files: `download_files(attachments)`
    8. extract files from archives: `extract_files(folder)`
    9. read in individual CSV files, concatenate them and output results: `merge_files(folder)`

The only real PITA was figuring out how to get HubSpot's "token" as seamlessly as possible. After experimenting with this for quite some time I've reduced that portion of the script to the bare minimum: the first HTTP request will provide the website with the username and password, and the second one will verify that you're logged in (and in the process fetch the "token").

A very important feature of the code was that it shouldn't rely on any custom Python modules. It will run on *any* plain-vanilla Python installation that comes with macOS (tested with El Capitan and Sierra, both use Python 2.7). This explains why I didn't go the OAuth2 route (i.e. use `gmail-oauth2-tools` module) and why I stuck to `urllib2` instead of more modern `requests` for talking to the HubSpot server. Same goes for `pandas` vs. my homemade `merge_files()` function. The lack of OAuth2 means you will need to [enable Gmail access for less secure apps](https://www.google.com/settings/security/lesssecureapps). I guess that's one more reason for having a separate Gmail account just for this...

Last time (sometime in Q4 2016?) I checked the scripts worked just fine, but again, due to their hacky nature they could be broken at any time. YMMV!

## TO-DO:

    - I should probably rewrite the merge function at some point just so that it'll be more elegant...
