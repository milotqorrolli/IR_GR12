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
        search_result[word] = [(filenames[position], position) for position in inverted_index[word]]
    else:
        return None  # Return None if no occurrences of the word are found
    return search_result

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("files[]")
        search_term = request.form.get("search_term")
        if files:
            try:
                inverted_index = {}
                filenames = {}
                all_words = {}
                for file in files:
                    filename = file.filename
                    text = file.read().decode("utf-8")
                    tokens = tokenize(text)
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
                return render_template("index.html", search_result=search_result, all_words=all_words)
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
