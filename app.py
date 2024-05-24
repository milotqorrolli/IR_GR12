from flask import Flask, render_template, request
import re
import math
import csv
import io

app = Flask(__name__)


def tokenize(text):
    words = re.findall(r"\b\w+\b", text.lower())
    return words


def build_inverted_index(tokens, file_index_offset):
    inverted_index = {}
    for i, token in enumerate(tokens):
        if token not in inverted_index:
            inverted_index[token] = [i + file_index_offset]
        else:
            inverted_index[token].append(i + file_index_offset)
    return inverted_index


def search_word(word, inverted_index, filenames):
    search_result = {}
    if word in inverted_index:
        search_result[word] = [
            (filenames[position], position) for position in inverted_index[word]
        ]
    else:
        return None
    return search_result


def calculate_tf(term_frequency, total_terms):
    return {term: round(freq / total_terms, 4) for term, freq in term_frequency.items()}


def calculate_idf(corpus, term_counts):
    num_documents = len(corpus)
    idf_values = {}
    for term, count in term_counts.items():
        doc_count = sum(1 for doc in corpus if term in doc)
        idf_values[term] = round(math.log(num_documents / (doc_count)), 2)
    return idf_values


def calculate_tf_idf(tf, idf):
    return {term: round(tf[term] * idf.get(term, 0), 4) for term in tf}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("files[]")
        search_term = request.form.get("search_term")

        # Reset variables
        corpus = []
        inverted_index = {}
        filenames = {}
        all_words = {}
        term_counts = {}
        tf_all = {}
        tf_idf_all = {}
        file_index_offset = 0

        if files:
            try:
                for file in files:
                    filename = file.filename
                    file_extension = filename.rsplit(".", 1)[1].lower()

                    if file_extension == "txt":
                        text = file.read().decode("utf-8")
                        tokens = tokenize(text)
                        corpus.append(tokens)
                        total_terms = len(tokens)
                        term_frequency = {}
                        for token in tokens:
                            term_frequency[token] = term_frequency.get(token, 0) + 1
                        tf_all[filename] = calculate_tf(term_frequency, total_terms)
                        for token, count in term_frequency.items():
                            term_counts[token] = term_counts.get(token, 0) + count

                        file_index = build_inverted_index(tokens, file_index_offset)
                        for word, positions in file_index.items():
                            if word in inverted_index:
                                inverted_index[word].extend(positions)
                            else:
                                inverted_index[word] = positions
                            all_words.setdefault(word, []).append((filename, positions))

                        filenames.update(
                            {
                                position: filename
                                for position in range(
                                    file_index_offset, file_index_offset + len(tokens)
                                )
                            }
                        )
                        file_index_offset += len(tokens)

                    elif file_extension == "csv":
                        with io.TextIOWrapper(
                            file.stream, encoding="utf-8"
                        ) as csv_file:
                            csv_reader = csv.reader(csv_file)
                            for row in csv_reader:
                                text = " ".join(row)
                                tokens = tokenize(text)
                                corpus.append(tokens)
                                total_terms = len(tokens)
                                term_frequency = {}
                                for token in tokens:
                                    term_frequency[token] = (
                                        term_frequency.get(token, 0) + 1
                                    )
                                tf_all[filename] = calculate_tf(
                                    term_frequency, total_terms
                                )
                                for token, count in term_frequency.items():
                                    term_counts[token] = (
                                        term_counts.get(token, 0) + count
                                    )

                                file_index = build_inverted_index(
                                    tokens, file_index_offset
                                )
                                for word, positions in file_index.items():
                                    if word in inverted_index:
                                        inverted_index[word].extend(positions)
                                    else:
                                        inverted_index[word] = positions
                                    all_words.setdefault(word, []).append(
                                        (filename, positions)
                                    )

                                filenames.update(
                                    {
                                        position: filename
                                        for position in range(
                                            file_index_offset,
                                            file_index_offset + len(tokens),
                                        )
                                    }
                                )
                                file_index_offset += len(tokens)

                idf = calculate_idf(corpus, term_counts)

                for filename, tf in tf_all.items():
                    tf_idf_all[filename] = calculate_tf_idf(tf, idf)

                if search_term:
                    search_result = search_word(search_term, inverted_index, filenames)
                    all_words = None
                    if not search_result:
                        return render_template(
                            "index.html",
                            error=f"No occurrences of '{search_term}' found in any document.",
                        )
                else:
                    search_result = None

                return render_template(
                    "index.html",
                    search_result=search_result,
                    all_words=all_words,
                    tf_all=tf_all,
                    idf=idf,
                    tf_idf_all=tf_idf_all,
                )

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
