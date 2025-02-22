import re
import emoji
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
import pandas as pd
import tkinter as tk
from tkinter import scrolledtext
from PIL import ImageTk, Image

API_KEY = 'AIzaSyD8MI3Jjebzds4VZojWe7-_5o4GvJfcn7c'
youtube = build('youtube', 'v3', developerKey=API_KEY)

def fetch_comments(video_id):
    comments = []
    nextPageToken = None
    while len(comments) < 600:
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=100,
            pageToken=nextPageToken
        )
        response = request.execute()
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            # Remove <br> tags and emojis from the comment text
            comment_text = comment['textDisplay'].replace('<br>', '')
            comment_text = emoji.demojize(comment_text)
            comments.append(comment_text)
        nextPageToken = response.get('nextPageToken')

        if not nextPageToken:
            break
    return comments


def analyze_sentiment(comments):
    hyperlink_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    threshold_ratio = 0.65
    relevant_comments = []

    for comment_text in comments:
        comment_text = comment_text.lower().strip()

        emojis = emoji.emoji_count(comment_text)

        text_characters = len(re.sub(r'\s', '', comment_text))

        if (any(char.isalnum() for char in comment_text)) and not hyperlink_pattern.search(comment_text):
            if emojis == 0 or (text_characters / (text_characters + emojis)) > threshold_ratio:
                relevant_comments.append(comment_text)

    f = open("ytcomments.txt", 'w', encoding='utf-8')
    for idx, comment in enumerate(relevant_comments):
        f.write(str(comment) + "\n")
    f.close()

    analyzer = SentimentIntensityAnalyzer()
    polarity = []
    positive_comments = []
    negative_comments = []
    neutral_comments = []

    for index, items in enumerate(relevant_comments):
        sentiment_dict = analyzer.polarity_scores(items)
        polarity.append(sentiment_dict['compound'])

        if polarity[-1] > 0.05:
            positive_comments.append(items)
        elif polarity[-1] < -0.05:
            negative_comments.append(items)
        else:
            neutral_comments.append(items)

    avg_polarity = sum(polarity) / len(polarity)
    if avg_polarity > 0.05:
        avg_sentiment = "Positive"
    elif avg_polarity < -0.05:
        avg_sentiment = "Negative"
    else:
        avg_sentiment = "Neutral"

    # Save all comments to a single Excel file
    comments_df = pd.DataFrame({'Comments': relevant_comments,
                                'Sentiment': ['Positive' if p > 0.05 else 'Negative' if p < -0.05 else 'Neutral' for p in polarity]})
    comments_df.to_excel('all_comments.xlsx', index=False)

    return positive_comments, negative_comments, neutral_comments

def analyze_video():
    video_id = video_id_entry.get()[-11:]
    comments = fetch_comments(video_id)
    positive_comments, negative_comments, neutral_comments = analyze_sentiment(comments)
    all_comments_text.delete('1.0', tk.END)
    all_comments_text.insert(tk.END, "\n".join(comments))
    positive_comments_text.delete('1.0', tk.END)
    positive_comments_text.insert(tk.END, "\n".join(positive_comments))
    negative_comments_text.delete('1.0', tk.END)
    negative_comments_text.insert(tk.END, "\n".join(negative_comments))
    neutral_comments_text.delete('1.0', tk.END)
    neutral_comments_text.insert(tk.END, "\n".join(neutral_comments))

def show_bar_chart():
    labels = ['Positive', 'Negative', 'Neutral']
    comment_counts = [len(positive_comments_text.get("1.0", tk.END).split('\n')), 
                      len(negative_comments_text.get("1.0", tk.END).split('\n')),
                      len(neutral_comments_text.get("1.0", tk.END).split('\n'))]
    total_comments = sum(comment_counts)
    percentages = [count / total_comments * 100 for count in comment_counts]
    
    plt.bar(labels, comment_counts, color=['blue', 'red', 'grey'])
    plt.xlabel('Sentiment')
    plt.ylabel('Comment Count')
    plt.title('Sentiment Analysis of Comments')
    
    for i, count in enumerate(comment_counts):
        plt.text(i, count + 1, f'{percentages[i]:.1f}%', ha='center')
    
    plt.show()


def show_pie_chart():
    labels = ['Positive', 'Negative', 'Neutral']
    comment_counts = [len(positive_comments_text.get("1.0", tk.END).split('\n')), 
                      len(negative_comments_text.get("1.0", tk.END).split('\n')),
                      len(neutral_comments_text.get("1.0", tk.END).split('\n'))]
    plt.figure(figsize=(6, 6))
    plt.pie(comment_counts, labels=labels, autopct='%1.1f%%')
    plt.title('Sentiment Analysis of Comments')
    plt.show()

root = tk.Tk()
root.title("YouTube Comment Analysis")

# Background Image
bg_image = Image.open("D:\Final GUI\yt_back.jpg")
bg_image = bg_image.resize((1600, 1200))
bg_photo = ImageTk.PhotoImage(bg_image)
bg_label = tk.Label(root, image=bg_photo)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)

video_id_label = tk.Label(root, text="Enter YouTube Video URL:")
video_id_label.place(x=20, y=20)

video_id_entry = tk.Entry(root, width=50)
video_id_entry.place(x=180, y=20)

analyze_button = tk.Button(root, text="Analyze", command=analyze_video)
analyze_button.place(x=650, y=20)

all_comments_label = tk.Label(root, text="All Extracted Comments:")
all_comments_label.place(x=20, y=60)

all_comments_text = scrolledtext.ScrolledText(root, width=50, height=35)
all_comments_text.place(x=20, y=100)

positive_comments_label = tk.Label(root, text="Positive Comments:")
positive_comments_label.place(x=500, y=60)

positive_comments_text = scrolledtext.ScrolledText(root, width=60, height=12)
positive_comments_text.place(x=500, y=100)

negative_comments_label = tk.Label(root, text="Negative Comments:")
negative_comments_label.place(x=500, y=300)

negative_comments_text = scrolledtext.ScrolledText(root, width=60, height=12)
negative_comments_text.place(x=500, y=340)

neutral_comments_label = tk.Label(root, text="Neutral Comments:")
neutral_comments_label.place(x=500, y=540)

neutral_comments_text = scrolledtext.ScrolledText(root, width=60, height=10)
neutral_comments_text.place(x=500, y=580)

bar_chart_button = tk.Button(root, text="Show Bar Chart", command=show_bar_chart)
bar_chart_button.place(x=1150, y=120)

pie_chart_button = tk.Button(root, text="Show Pie Chart", command=show_pie_chart)
pie_chart_button.place(x=1150, y=180)

root.mainloop()
