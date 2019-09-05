from selenium import webdriver
from selenium.webdriver.support import ui
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.common.exceptions import NoSuchWindowException, TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
from read_csv import gen_group_list, create_prompt
#from simplecrypt import encrypt, decrypt
#from gen_creds import read_conf
import os
import csv
import sys
#import getpass
import time
import re
import random
import datetime
import argparse

#TODO when multiple items in dropdown, hwo to go to each
#visit group url and post on group page specifically

def page_loaded(driver):
  return driver.find_element_by_tag_name("body") != None

def wait_elem(driver,xpath):
    timeout=5
    try:
        element_present = EC.presence_of_element_located((By.XPATH, xpath))
        element = WebDriverWait(driver, timeout).until(element_present)
        return element
    except TimeoutException:
        print("Timed out waiting for page to load")

def login(driver,name,username,password):
    # Opening the web browser
    # Finding email and password fields and sending the keys
    #driver.get('https://www.facebook.com/'+ name)
    driver.get("https://www.facebook.com/events/466616620431708/")
    time.sleep(1)
    email = driver.find_element_by_xpath("//input[@name='email']")#driver.find_element_by_id("email")
    email.send_keys(username)
    pwd = driver.find_element_by_xpath("//input[@name='pass']")#find_element_by_id("pass")
    pwd.send_keys(password)
    pwd.send_keys(Keys.RETURN)
    time.sleep(1)

def share_event_via_page(driver,group_url,message):
    driver.get(group_url)
    post_box = driver.find_element_by_xpath("//a[@data-tooltip-content='Write Post']")
    post_box.click()
    time.sleep(1)
    post_pop_up = driver.find_element_by_xpath("//div[@data-testid='react-composer-root']")
    post_field = post_pop_up.find_element_by_xpath("//div[contains(.,'Write something...')]")
    poster = post_field.find_element_by_xpath('.//ancestor::div[5]')
    poster.send_keys(message)

def share_event(driver,group_name,message):
    #TODO handle cases with duplicate names

    #Open 'share' pop-up and naviagate through drop-downa
    print('Sharing Event to '+group_name)
    share_button = driver.find_element_by_xpath("//a[@aria-label='Share']")
    share_button.click()
    time.sleep(1)
    share_as_post = driver.find_element_by_xpath("//a[@data-testid='event-share-in-newsfeed-option']")
    share_as_post.click()
    time.sleep(1)
    select_share_type = driver.find_element_by_xpath("//div[@data-testid='react_share_dialog_audience_selector']")
    select_share_type.click()
    time.sleep(1)
    share_in_group = driver.find_element_by_xpath("//span[@data-testid='share_to_group']/ancestor::li[contains(@role, 'presentation')]")
    share_in_group.click()
    #time.sleep(2)

    #Enter sharing message/prompt
    event_share_prompt = driver.find_element_by_xpath("//div[@data-testid='status-attachment-mentions-input']")
    event_share_prompt.send_keys(message)
    #time.sleep(2)

    #Enter group name
    group_name=group_name+' '
    total = len(group_name)+1
    for i in range(1,total):
        group_name_field = driver.find_element_by_xpath("//input[@data-testid='searchable-text-input']")
        group_name_field.click()
        group_name_field.send_keys(group_name[0:i])
        time.sleep(1)
        dropdown_results = driver.find_element_by_id('ariaPoliteAlert').text
        drop = int(dropdown_results.split(' ')[1])
        if dropdown_results=='Found 0 results':
            print('Group name is a typo or no longer exists!')
            return 0
        elif int(dropdown_results.split(' ')[1])>1:
            if i==total-1:
                return drop
            continue
        elif int(dropdown_results.split(' ')[1])==1: #if only one result
            group_name_field.send_keys(Keys.DOWN)
            group_name_field.send_keys(Keys.ENTER)
            break
        else:
            return 0

    time.sleep(1)
    #time.sleep(3)
    post_button = driver.find_element_by_xpath("//button[@data-testid='react_share_dialog_post_button']")
    post_button.click()
    time.sleep(1)
    #wait_elem(driver,"//span[contains(.,'Settings')]")
    try:
        confirmation_element = driver.find_element_by_xpath("//span[contains(.,'This was successfully shared with')]")
        print('Event is shared!')
        return 1
    except NoSuchElementException as e:
        print(e)
        print('Event was not shared to group!')
        try:
            confirmation_element = driver.find_element_by_xpath("//span[contains(.,'This was sent')]")
            print('Event is pending admin approval')
            return 1
        except NoSuchElementException as e:
            print(e)
            print('There was a problem with posting, skipping this group!')
            return 0
'''
    if confirmation_element.is_displayed():
        print('CONFIRMED')
        status=1
    else:
        status=0
    return status
'''
def attempter(func,args,error,num_attempts=5,sleep_time=1): #error can be tuple of errors
    status=0
    for attempt in range(num_attempts):
        try:
            status=func(*args)
            time.sleep(sleep_time)
            if status!=1:
                status=0
        except ElementClickInterceptedException:
            continue
        except ElementNotInteractableException:
            continue
        except NoSuchElementException:
            continue
        except error as e:
            print(e)
            continue
        break
    else:
        print(attempt) #Failure case
    return status

#Might need these actions later
#actions = ActionChains(driver)
#actions.send_keys(Keys.ENTER)
#actions.perform()

def main():
    #event_url = sys.argv[1]
    #group_csv = sys.argv[2]

    parser = argparse.ArgumentParser()
    parser.add_argument("-email","--email",help="FB Email")
    parser.add_argument("-pass","--password",help="FB Password")
    parser.add_argument("-eventurl","--groupurl",help="FB group URL")
    parser.add_argument("-csv","--csv",help="csv")
    parser.add_argument("-firstname","--firstname",help="First Name")
    parser.add_argument("-lastname","--lastname",help="Last Name")
    args = parser.parse_args()

    #Initialize webdriver
    _browser_profile = webdriver.FirefoxProfile()
    _browser_profile.set_preference("dom.webnotifications.enabled", False)
    #binary = FirefoxBinary('Users/ryans/Code/marketing_auto_share/geckodriver')
    driver = webdriver.Firefox(firefox_profile=_browser_profile)
    driver.implicitly_wait(12)
    #Login to Fb then navigate to event page
    dotname = args.firstname + '.' + args.lastname 
    login(driver,dotname,dotname,args.password)
    event_url = args.groupurl
    group_csv = args.csv
    driver.get(event_url)

    #group_url = "https://www.facebook.com/groups/263023754274933/"
    #message='test'
    #share_event_via_page(group_url,message)

    #time.sleep(1)
    #message = 'THIS IS AUTOMATED, GIMME DAT GURT TYLER post#'
    #group_name ='Test_group_1'
    #prompt = 'Hey [GROUPDESC]! Come on down to Freewheel Brewing [LOCATIONDESC] for a free stand-up comedy show featuring some of the best comedians in the Bay! Hosts Ryan Goodcase and Ryan Sudhakaran (me) will be serving a comedy flight for all tastes, whether it be dry, wit, or incredibly bitter. So grab a brew, sit back, and enjoy some Good Suds!'
    #prompt = 'Hey [GROUPDESC]! This is a FREE comedy show that my friends and I run in [LOCATIONDESC]. The show takes place every other Saturday in a super hip wood-shop (Studio by Terra Amico), and features some hilarious local and touring comedians. Also there is awesome craft beer next door at Hapas Brewery!\n\nSo come on down to drink and laugh at Super Stacked!\nFB Page: https://www.facebook.com/SuperStacked/'
    #prompt=('''Hey [GROUPDESC]! This is a FREE comedy show that my friends and I run in [LOCATIONDESC]. The show takes place every other Saturday in a super hip wood-shop (Studio by Terra Amico), and features some hilarious local and touring comedians. Also there is awesome craft beer next door at Hapas Brewery!
    #\n\n
    ##So come on down to drink and laugh at Super Stacked!
    #FB Page: https://www.facebook.com/SuperStacked/
    #''')

    #a = "Hey [GROUPDESC]! Come on down to the only comedy show in a woodshop! The show takes place every other Saturday at the Studio by Terra Amico [LOCATIONDESC], and features some of the Bay Area’s best local and touring comedians. Also there is awesome craft beer next door at Hapas Brewery!\n"
    #b = "So come on down to drink and laugh at Super Stacked!"
    #c = "FB Page: https://www.facebook.com/SuperStacked/"
    #prompt = "%s\n\n%s\n%s" % (a,b,c)

    ####
    #a = "Hey [GROUPDESC]! Speak Easy is a not-so-secret comedy show in the backroom of Clandestine Brewing in [LOCATIONDESC]. The show is completely free and features some of the best local and touring comedians the bay area has to offer! So come on down, grab a brew and enjoy some un-prohibited stand-up comedy!\n"
    #b = "FB Page: https://www.facebook.com/speakeasycomedyshow/"
    #c = ""
    #prompt = "%s\n\n%s\n%s" % (a,b,c)
    ####
    a = "Hey [GROUPDESC]! Come on down to Freewheel Brewing [LOCATIONDESC] for a free stand-up comedy show featuring some of the best comedians in the Bay! Hosts Ryan Goodcase and Ryan Sudhakaran (me) will be serving a comedy flight for all tastes, whether it be dry, wit, or incredibly bitter. So grab a brew, sit back, and enjoy some Good Suds!\n"
    b = "FB Page: https://www.facebook.com/GoodSuds/"
    c = ''
    prompt = "%s\n\n%s\n%s" % (a,b,c)
    #group_prompt_list = get_prompt_list('goodsuds.csv',prompt)
    group_list = gen_group_list(group_csv)
    print(group_list)
    #group_prompt_list = get_prompt_list('goodsuds.csv',prompt)
    #group_list = gen_group_list('group_csv')
    for group_tuple in group_list:
        #group_name, group_prompt = group_tuple[0],group_tuple[1]
        group_name, group_desc, loc_desc,posted = group_tuple[0],group_tuple[1],group_tuple[2],group_tuple[3]
        print('Checking '+group_name)
        print(posted)
        if group_name=='' or posted in ['Yes','yes']:
            print('Already Posted!')
            continue
        elif posted not in ['no','No','NO']:
            print ('More than one group of similar name')
            continue
        else:
            pass
        group_prompt = create_prompt(prompt,group_desc,loc_desc)
        share_status = attempter(share_event,[driver,group_name,group_prompt],error=NoSuchWindowException,sleep_time=2)
        print(share_status)
        #share_event(group_name,group_prompt)
        if share_status==1:
            group_tuple[3]='yes'
            writer = csv.writer(open(group_csv, 'w'))
            writer.writerows(group_list)
        elif share_status>1:
            group_tuple[3]=share_status
            writer = csv.writer(open(group_csv, 'w'))
            writer.writerows(group_list)
        else:
            pass
        retry_status = attempter(driver.get,[event_url],error=ConnectionResetError,sleep_time=3)
        if retry_status==0:
            continue
        #driver.implicitly_wait(5)

    '''
        for attempt in range(num_tries):
            try:
                driver.get(event_url)
                time.sleep(1)
            except (ConnectionResetError,NoSuchWindowException) as e:
                print(e)
                continue
                print(attempt) #Failure case
            break
        #driver.implicitly_wait(5)
    '''
    #driver.close()
main()