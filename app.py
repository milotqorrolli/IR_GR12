from flask import Flask, render_template, request
import re
import math

app = Flask(__name__)

def tokenize(text):
    words = re.findall(r"\b\w+\b", text.lower())
    return words

def build_inverted_index(tokens):
    inverted_index = {}
    for i, token in enumerate(tokens):
        if token not in inverted_index:
            inverted_index[token] = [i]
        else:
            inverted_index[token].append(i)
    return inverted_index

def search_word(word, inverted_index, filenames):
    search_result = {}
    if word in inverted_index:
        search_result[word] = [(filenames[position], position) for position in inverted_index[word]]
    else:
        return None  
    return search_result

def calculate_tf(term_frequency):
    max_freq = sum(term_frequency.values())
    return {term: round(freq / max_freq, 2) for term, freq in term_frequency.items()}


def calculate_idf(corpus, term_counts):
    num_documents = len(corpus)
    idf_values = {}
    for term, count in term_counts.items():
        doc_count = sum(1 for doc in corpus if term in doc)
        idf_values[term] = round(math.log(num_documents / (doc_count)),2)
    return idf_values

def calculate_tf_idf(tf, idf):
    return {term: tf[term] * idf.get(term, 0) for term in tf}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("files[]")
        search_term = request.form.get("search_term")
        if files:
            try:
                corpus = []  
                inverted_index = {}
                filenames = {}
                all_words = {}
                term_counts = {}  
                tf_all = {}  
                tf_idf_all = {}  
                for file in files:
                    filename = file.filename
                    text = file.read().decode("utf-8")
                    tokens = tokenize(text)
                    corpus.append(tokens)
                    term_frequency = {}
                    for token in tokens:
                        term_frequency[token] = term_frequency.get(token, 0) + 1
                    tf_all[filename] = calculate_tf(term_frequency)  
                    term_counts.update(term_frequency)  
                    file_index = build_inverted_index(tokens)
                    for word, positions in file_index.items():
                        if word in inverted_index:
                            inverted_index[word].extend(
                                [position + len(inverted_index) for position in positions]
                            )
                        else:
                            inverted_index[word] = [position for position in positions]
                        all_words.setdefault(word, []).append((filename, positions))
                    filenames.update(
                        {len(filenames) + idx: filename for idx in range(len(tokens))}
                    )
                
                idf = calculate_idf(corpus, term_counts)
                
                for filename, tf in tf_all.items():
                    tf_idf_all[filename] = calculate_tf_idf(tf, idf)

                if search_term:
                    search_result = search_word(search_term, inverted_index, filenames)
                    all_words = None 
                    if not search_result:
                        return render_template(
                            "index.html",
                            error=f"No occurrences of '{search_term}' found in any document."
                        )
                else:
                    search_result = None
                return render_template("index.html", search_result=search_result, all_words=all_words, tf_all=tf_all, idf=idf, tf_idf_all=tf_idf_all)
            except Exception as e:
                return render_template(
                    "index.html", error=f"Error processing file: {str(e)}"
                )
        else:
            return render_template("index.html", error="No files uploaded")
    else:
        return render_template("index.html")


    
if __name__ == "__main__":
    app.run(debug=True)
