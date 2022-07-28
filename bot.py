"""Automatically download Twitch Clips, merge them and upload to YouTube as single Video"""
import os
import random
import re
import requests

import cv2

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from moviepy.editor import *
from progress.bar import Bar

import uploadVideo


CLIPPATH = './clips/'
for f in os.listdir(CLIPPATH):
    os.remove(CLIPPATH + f)

for f in os.listdir('./output/'):
    os.remove('./output/' + f)

driver = webdriver.Edge(executable_path='./msedgedriver')
driver.get('https://streamscharts.com/clips?language=de')

for i in range(5):
    moreBtn = WebDriverWait(
        driver,
        10).until(
        EC.element_to_be_clickable(
            driver.find_element(
                By.XPATH,
                "/html/body/main/div[2]/div/div[2]/div[1]/div[2]/button")))
    driver.execute_script('arguments[0].click()', moreBtn)

videos = []
COUNTER = 1
print('Looking up the hottest Clips:')
barCollectVideos = Bar('Processing', max=30)
while len(videos) < 30:
    try:
        elem = WebDriverWait(
            driver,
            10).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 f"/html/body/main/div[2]/div/div[2]/div[1]/div[1]/div[3]/button[{COUNTER}]")))
        timestr = elem.find_element(
            By.XPATH,
            f"/html/body/main/div[2]/div/div[2]/div[1]/div[1]/div[3]/button[{COUNTER}]/div[3]/div[1]/div[2]/span").text
        minint = int(timestr.split(':')[0])
        secint = int(timestr.split(':')[1])
        COUNTER += 1
        if minint != 0 or secint > 35:
            continue
        videos.append(re.search("(?P<url>https?://[^\\s]+)", elem.get_attribute(
            'x-on:click')).group("url").replace('embed?clip=', '')[:-2])
        barCollectVideos.next()
    except Exception as e:
        print(e)

barCollectVideos.finish()
links = []

print('Extracting those sweet download links:')
barCollectLinks = Bar("Processing", max=len(videos))
for video in videos:
    driver.get('https://clipsey.com')
    searchbox = driver.find_element(
        By.XPATH, "/html/body/div[2]/div/div[3]/div/div[1]/div/div[1]/input")
    searchbox.send_keys(video)
    driver.find_element(
        By.XPATH,
        "/html/body/div[2]/div/div[3]/div/div[1]/div/div[1]/button").click()
    try:
        link = WebDriverWait(
            driver,
            10).until(
            EC.visibility_of_element_located(
                (By.XPATH,
                 "/html/body/div[2]/div/div[3]/div/div[1]/div/div[3]/div/div[1]/div/div[2]/a")))
        links.append(link.get_attribute('href'))
        barCollectLinks.next()
    except Exception as e:
        print(e)
barCollectLinks.finish()
driver.quit()

print('Downloading them clips:')
barDownloadVideos = Bar('Processing', max=len(videos))
for idx, link in enumerate(links):
    with open(f'{CLIPPATH}clip{idx}.mp4', 'wb', encoding='utf-8') as f:
        barDownloadVideos.next()
        f.write(requests.get(link).content)
barDownloadVideos.finish()

print('Converting clips to final video:')
videoFiles = []
for file in os.listdir('./clips'):
    clip = VideoFileClip(f'./clips/{file}').fx(afx.audio_normalize)
    videoFiles.append(clip)

PADDING = 1
finalVideoList = [videoFiles[0]]
idx = videoFiles[0].duration - PADDING
for video in videoFiles[1:]:
    finalVideoList.append(video.set_start(idx).crossfadein(PADDING))
    idx += video.duration - PADDING

final_video = concatenate_videoclips(clips=finalVideoList, method='chain')
final_video.write_videofile('./output/final.mp4', threads=8, fps=30)

print('Generating Thumbnail..')
vidcap = cv2.VideoCapture("./output/final.mp4")
totalFrames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
randomFrameNumber = random.randint(0, totalFrames)
vidcap.set(cv2.CAP_PROP_POS_FRAMES, randomFrameNumber)
success, image = vidcap.read()
if success:
    cv2.imwrite("./output/preThumbnail.png", image)

with open('stats.txt', 'r+', encoding='utf-8') as f:
    episode = int(f.readline())
    f.seek(0)
    f.write(str(episode + 1))
    f.truncate()

image = cv2.imread("./output/preThumbnail.png")
dimensions = image.shape
font = cv2.FONT_HERSHEY_SIMPLEX
text = f"Stream Clips #{episode}"

cv2.putText(
    img=image,
    text=text,
    org=(
        30,
        150),
    fontFace=cv2.FONT_HERSHEY_COMPLEX,
    fontScale=5,
    color=[
        0,
        0,
        0],
    lineType=cv2.LINE_AA,
    thickness=10)
cv2.putText(
    img=image,
    text=text,
    org=(
        30,
        150),
    fontFace=cv2.FONT_HERSHEY_COMPLEX,
    fontScale=5,
    color=[
        255,
        255,
        255],
    lineType=cv2.LINE_AA,
    thickness=5)
image = cv2.resize(image, (1280, 720))
cv2.imwrite("./output/thumbnail.png", image)

print('Starting YouTube Upload')
uploadVideo.startUpload(
    './output/final.mp4',
    f'Beste Deutsche Stream Clips #{episode}',
    'Wir zeigen euch die besten Clips, die Twitch Germany in dieser Woche hervorgebracht hat!',
    22,
    'twitch, beste, clips, deutschland, woche',
    'public')

print('DONE!')
