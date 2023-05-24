from youtubesearchpython import *
import random
import tweepy
import os
import io
import re
import time
import json
import warnings
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
print('running')
#API Creds
api_key = os.environ['API KEY']
api_secret = os.environ['API SECRET']
access_token = os.environ['ACCESS TOKEN']
access_token_secret = os.environ['ACCESS TOKEN SECRET']
api_key_stability = os.environ['STABILITY API KEY']

# Authenticate with the Twitter API using your API credentials
auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
api = tweepy.API(auth)

with open('tweeted.json') as f:
    data = json.load(f)
    mentions_list = data["mentions"]


def generate_image(user_prompt):
    stability_api = client.StabilityInference(
        key=api_key_stability, # API Key reference.
        verbose=True, # Print debug messages.
        engine="stable-diffusion-v1-5", # Set the engine to use for generation. 
    )
    # Set up our initial generation parameters.
    answers = stability_api.generate(
        prompt=user_prompt,
        seed=992446758,
        steps=30, # Amount of inference steps performed on image generation. 
        cfg_scale=8.0,
        width=512, # Generation width, defaults to 512 if not included.
        height=512, # Generation height, defaults to 512 if not included.
        samples=1, # Number of images to generate, defaults to 1 if not included.
        sampler=generation.SAMPLER_K_DPMPP_2M
    )
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Safety filter fail"
                    "Please modify the prompt and try again.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                img = Image.open(io.BytesIO(artifact.binary))
                name = user_prompt.replace(' ','')
                if len(name)>20:
                    name = name[0:20]
                name += '.png'
                img.save('images/'+name)
                return 'images/'+name

def save_last_tweet(file, Id):
    f = open(file, 'w')
    f.write(str(Id))
    f.close()
    print("Updated the file with the latest tweet Id")
    return

def respondToTweet():
    mentions = api.mentions_timeline()
    if len(mentions) == 0:
        print('nada')
        return
    else:
        #print(mentions)
        for mention in mentions[0:5]:
            text = str(mention)
            first_chop = text.split("'text':")[1]
            tweet_content = first_chop.split(',')[0]
            if '#prompt' in tweet_content and str(mention.id) not in mentions_list:    
                response = tweet_content.replace('#prompt','')
                response = response.replace('@SanjinDedic','')
                response = response.replace("'","")
                response = response.strip()
                filename = generate_image(response)
                image = api.media_upload(filename)
                mentions_list.append(str(mention.id))
                with open('tweeted.json', 'w') as f:
                    json.dump({"mentions": mentions_list}, f)
                my_status = 'Greetings to @' + str(mention.user.screen_name) + ' here is your image curtesty of #stablediffusion 1.5 '
                my_status += response 
                if len(my_status) > 279:
                    my_status = my_status[0:279]
                try:
                    api.create_favorite(mention.id)
                    api.update_status(status = my_status, media_ids=[image.media_id])
                except:
                    print('some error')
while True:
    respondToTweet()
    time.sleep(30)