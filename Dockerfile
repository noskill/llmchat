#Deriving the latest base image
FROM python:latest

env OPENAI_API_KEY=""
env SERPAPI_API_KEY=""
# install pip
RUN apt-get update && apt install -y pip

# install dependencies
RUN pip install langchain openai google-search-results wikipedia
RUN pip3 install torch --index-url https://download.pytorch.org/whl/cpu
# install sentencepiece from github
RUN apt install -y cmake
RUN rm -r sentencepiece/ ; git clone https://github.com/google/sentencepiece.git && cd sentencepiece/ && \
  mkdir build && cd build/ && cmake .. && make install
RUN pip install chromadb


# install vim
RUN apt install -y vim less


# Any working directory can be chosen as per choice like '/' or '/home' etc
WORKDIR /root/


#CMD instruction should be used to run the software
#contained by your image, along with any arguments.

CMD ["bash"]
