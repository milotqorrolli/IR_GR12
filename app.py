from flask import Flask, render_template, request
import re

app = Flask(__name__)


def tokenize(text):
    # Tokenize the text into words
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
        documents = set()  # Use a set to store unique document names
        for document_id in inverted_index[word]:
            documents.add(filenames[document_id])
        search_result[word] = list(documents)
    return search_result

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("files[]")
        search_term = request.form["search_term"]
        if files:
            try:
                inverted_index = {}
                filenames = {}
                for file in files:
                    filename = file.filename
                    text = file.read().decode("utf-8")
                    tokens = tokenize(text)
                    file_index = build_inverted_index(tokens)
                    print("File Index:", file_index)  # Print file index
                    for word, positions in file_index.items():
                        print("Word:", word)  # Print word
                        print("Positions:", positions)  # Print positions
                        if word in inverted_index:
                            inverted_index[word].extend(
                                [
                                    position + len(inverted_index)
                                    for position in positions
                                ]
                            )
                        else:
                            inverted_index[word] = [position for position in positions]
                        # print("Inverted Index:", inverted_index)  # Print inverted index
                    # Store filename corresponding to document index
                    filenames.update(
                        {len(filenames) + idx: filename for idx in range(len(tokens))}
                    )
                    print("Filenames:", filenames)  # Print filenames
                search_result = search_word(search_term, inverted_index, filenames)
                print("Search Result:", search_result)  # Print search result
                if not search_result:
                    return render_template(
                        "index.html",
                        error=f"No occurrences of '{search_term}' found in any document.",
                    )
                return render_template("index.html", search_result=search_result)
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
