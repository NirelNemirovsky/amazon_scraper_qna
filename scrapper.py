from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
import threading, queue
import json
import os, sys
from constants import questions_url, max_page_num, max_retries, timeout

"""
Scrapper class takes care of all regarding scraping the qna page using the product ASIN
It also manages to use UserAgent in order to access amazon as a scrapper and not to get banned
"""


class Scraper:
    def __init__(self, asin):
        """initialize a user agent generator, use it in order to not get blocked by amazon"""
        self.ua = UserAgent()
        self.asin = asin

    def scrape_qna(self):
        questions = self.retrieve_questions(self.asin)
        questions_list = list(questions.queue)

        print("found " + str(len(questions_list)) + " questions for product " + self.asin)

        """save questions to file"""
        if not ( os.path.exists('./questions') ) : os.makedirs('./questions')
        questions_file = open("./questions/" + self.asin + ".json", 'w+')

        for i in questions_list:
            json.dump(i, questions_file)
            questions_file.write('\n')

        questions_file.close()

    def retrieve_questions(self, asin):
        """Scrapes the questions pages and returns a list
            of dicts containing questions and respecitive answers"""

        threads = []
        results = queue.Queue()

        """for each page in the Q&A start a new thread to scan the html"""
        for page_num in range(1, max_page_num):
            t = threading.Thread(
                target=self.scrape_page_questions,
                args=(asin, page_num, results)
            )
            t.start()
            threads.append(t)

        for thread in threads:
            thread.join()

        return results

    def scrape_page_questions(self, asin, page_num, results):
        """threads to request and scrape a single questions page"""

        url = questions_url + asin + '/' + str(page_num)

        attempt = 0

        while attempt < max_retries:
            try:
                res = requests.get(url,
                                   timeout=timeout,
                                   headers={'User-Agent': self.ua.random}
                                   )

                if res.status_code != 200:
                    raise RuntimeError("Server not responding: status code " + str(res.status_code) + " for url " + url)
                else:
                    soup = BeautifulSoup(res.content, 'html.parser')
                    question_boxes = soup.find_all("div", {"class": "a-fixed-left-grid-col a-col-right"})

                    """numerates the questions by the question boxes as shown in the product html page"""
                    for j, box in enumerate(question_boxes):
                        q_a_dict = {}

                        """skip the 1st one, as this is not a real question"""
                        if (j == 0):
                            continue

                        for k, question in enumerate(box.find_all("div", {"class": "a-fixed-left-grid-col a-col-right"})):
                            if k == 0:
                                q_a_dict['question'] = question.a.text.strip()
                        for k, answer in enumerate(box.find_all("div", {"class": "a-fixed-left-grid-col a-col-right"})):
                            if k != 0:
                                if answer.find("span", {"class": "askLongText"}):
                                    ranswer = answer.find("span", {"class": "askLongText"}).text
                                    ranswer = ranswer.strip()[:-8]
                                else:
                                    ranswer = answer.span.text
                                q_a_dict['answer'] = ranswer.strip()
                        if 'answer' in q_a_dict and 'question' in q_a_dict:
                            results.put(q_a_dict)

                    return

            except requests.exceptions.Timeout:
                print("Connection timed out for url " + url)
            except requests.exceptions.RequestException as err:
                print(err)
            except RuntimeError as err:
                print(err)
            except KeyboardInterrupt:
                print('Keyboard interrupt received')
                sys.exit()
            attempt += 1

        print("failed url " + url + " after several attempts")
