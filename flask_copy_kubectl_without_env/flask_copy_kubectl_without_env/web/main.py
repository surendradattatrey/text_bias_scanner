from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import re

app = Flask(__name__)
df_tokens = pd.read_csv('v3_tokens.csv')


def bias_words():
    """
    Getting bias word from v3_tokens
    :return:bias words
    """

    list_word = [w.lower().strip() for w in list(df_tokens['Token'])]
    biased_word_list = list(set(list_word))
    return biased_word_list


def replacement_fun():
    """
    Getting replacement dictionary
    :return:dictionary with replacement word(s)
    """

    df_tokens['Token'] = df_tokens['Token'].str.lower()  # convert token to small case
    df_tokens['Token'] = df_tokens['Token'].str.strip()  # remove white spaces from token
    df_tokens['Word Replacement'] = df_tokens['Word Replacement'].str.lower()  # convert replacement word to small case
    df_tokens['Word Replacement'] = df_tokens['Word Replacement'].str.strip() # remove white space from replacement word
    df = df_tokens[['Token', 'Word Replacement']]  # new dataframe with Token & Word Replacement
    df['Word Replacement'] = df['Word Replacement'].replace(np.nan, "No Replacement") # handling NaN
    df_groupby = df.groupby('Token', as_index=False)['Word Replacement'].apply(','.join) #group by on Token values
    df_groupby['Word Replacement'] = df_groupby['Word Replacement'].str.replace(r',*No Replacement,*', '')
    t = df_groupby.loc[1, 'Word Replacement']
    df_groupby = df_groupby[df_groupby['Word Replacement'] != t]
    df_groupby_dict = df_groupby.set_index('Token').T.to_dict('list') # converting groupby output to dictionary
    dict_result = {}
    for key, value in df_groupby_dict.items():
        if key in total_word_found:
            dict_result[key] = value[0]
    return dict_result


@app.route("/")
def first_page():
    """
    Redirecting to first page
    :return:template
    """
    return render_template("page_first_copy.html")


@app.route('/result', methods=["POST", "GET"])
def result():
    """
    Redirecting to second page
    :return:template
    """
    data = request.form['text']
    jsdata2 = data
    jsdata = preprocessing_data(data)
    global table_string_html
    dict_replacement = replacement_fun()
    table_string_html = design_table(dict_replacement)
    var_script_close_window = '''function
    close_window()
    {
       window.open('http://localhost:5000/result','_self','');
       window.close();
    }'''
    return render_template('second_page_copy.html', data=jsdata, table_data=table_string_html)


def preprocessing_data(jsdata):
    """
    Getting the data from first page and logic of all processing
    :return: Dummy value
    """
    data_processing = jsdata
    data_processing = re.sub(r'\W+', ' ', data_processing)
    data_processing = data_processing.replace("�", "'")
    data_processing = data_processing.replace("\r\n", "")
    list_text = data_processing.split(" ")
    list_text = [w.lower() for w in list_text]
    list_word = bias_words()
    word_present_string = []
    for i in list_word:
        if i.lower() in jsdata.lower():
            word_present_string.append(i)
    highlight_data = [ele for ele in word_present_string if ele.lower() in list_word]

    # Checking for the words preceded and succeded by space.
    for i in jsdata.split(" "):
        if i.lower() in highlight_data:
            jsdata = jsdata.replace(" "+i+" ", " "+'<span style="background-color:#65B4D7;">'+i+'</span>'+" ")

    # Checking for the first word in the text
    first_word = jsdata.split(" ")[0]
    if first_word.lower()in highlight_data:
        jsdata = jsdata.replace(first_word + " ", '<span style="background-color:#65B4D7;">' + first_word + '</span>'
                                + " ")

    # Checking for the words followed by fullstop
    last_words_fullstop = re.findall(r'[A-Za-z0-9-_]*\.', jsdata, re.I)
    last_words_fullstop = [word[0:-1] for word in last_words_fullstop]
    words_to_highlight_fullstop = [word+"." for word in last_words_fullstop if word.lower() in list_word]
    for i in words_to_highlight_fullstop:
        jsdata = jsdata.replace(" " + i[0:-1] + ".", " " + '<span style="background-color:#65B4D7;">' + i[0:-1] +
                                '</span>' + ".", re.IGNORECASE)
    words_to_highlight_fullstop = [word for word in last_words_fullstop if word.lower() in list_word]

    # Checking for the words at the start of sentence preceded by \n and followed by space
    first_words_space = re.findall(r'\n+[A-Za-z0-9%&+^!@#$*(-_]*\s+', jsdata, re.I)
    first_words_space = [word[1:len(word)-1] for word in first_words_space]
    words_to_highlight_first_word = [word for word in first_words_space if word.lower() in list_word]
    for i in words_to_highlight_first_word:
        jsdata = jsdata.replace('\n'+re.escape(i) + " ",
                                "\n"+'<span style="background-color:#65B4D7;">'+re.escape(i) + '</span>' + " ",
                                re.IGNORECASE)

    # Checking for the words at the start of sentence \r\n and followed by space
    first_words_preceded_newline = re.findall(r'[\r\n]*[A-Za-z0-9%&+^!@#$*(-_]*\s+', jsdata, re.I)
    first_words_preceded_newline = [word[0:len(word)-1] for word in first_words_preceded_newline]
    first_words_preceded_newline_final = [re.sub(r'[\n\r\t<]', '', c) for c in first_words_preceded_newline]
    words_to_highlight_first_word_preceded_newline = [word for word in first_words_preceded_newline_final
                                                      if word.lower() in list_word]
    for i in words_to_highlight_first_word_preceded_newline:
        jsdata = jsdata.replace('\r\n' + re.escape(i) + " ",
                                "\r\n" + '<span style="background-color:#65B4D7;">' + re.escape(i) + '</span>' + " ",
                                re.IGNORECASE)

    # Checking word followed and preceded by special character
    pattern = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '+', '=', '{', '}',
               "'", ':', '"', '\\', '|', ';', ',', '.', '/', '?']  # list of special characters

    pattern_to_find = r'[!@#$%^&*()+={}\':"\\|;,.<>/?\s]*[A-Za-z0-9]*[!@#$%^&*()+={}\':"\\|;,.<>/?]*'
    word_followed_by_special_character = re.findall(pattern_to_find, jsdata, re.I)
    word_followed_by_special_character_clean = [ele.strip() for ele in word_followed_by_special_character]
    word_followed_by_special_character_clean = [re.sub(r'[\n\r\t<()!@#$%^&*+={}\':"\\|;,.>/?\s]', '', c)
                                                for c in word_followed_by_special_character_clean]
    word_followed_by_special_character_final = [word for word in word_followed_by_special_character_clean
                                                if word.lower() in list_word]
    for i in word_followed_by_special_character_final:
        for pat_start in pattern:
            for pat_end in pattern:
                pattern_to_find = str(pat_start)+str(i)+str(pat_end)
                if pattern_to_find in jsdata:
                    jsdata = jsdata.replace(str(pat_start)+re.escape(i)+str(pat_end),
                                            str(pat_start)+'<span style="background-color:#65B4D7;">' + re.escape(i) +
                                            '</span>'+str(pat_end), re.IGNORECASE)

    # Checking for the words preceded by space and followed by new line
    space_words_newline = re.findall(r'\s*[A-Za-z0-9%&+^!@#$*(-_]*\n*', jsdata, re.I)
    space_words_newline = [word.strip() for word in space_words_newline]
    space_words_newline_clean = [re.sub(r'[!@#$%^&*()<>+={},":\\|;,.\'/?]', '', c) for c in space_words_newline]
    space_words_newline_clean_final = [word for word in space_words_newline_clean if
                                       word.lower() in list_word]
    for i in space_words_newline_clean_final:
        jsdata = jsdata.replace(' ' + re.escape(i) + "\n",
                                " " + '<span style="background-color:#65B4D7;">' + re.escape(i) + '</span>' + "\n",
                                re.IGNORECASE)

    # Checking for the words preceded by space and followed by \r\n
    space_words_newline_rn = re.findall(r'\s*[A-Za-z0-9%&+^!@#$*(-_]*[\r\n]*', jsdata, re.I)
    space_words_newline_rn = [word.strip() for word in space_words_newline_rn]
    space_words_newline_rn_clean = [re.sub(r'[!@#$%^&*()<>+={},":\\|;,.\'/?]', '', c) for c in space_words_newline_rn]
    space_words_newline_clean_rn_final = [word for word in space_words_newline_rn_clean if
                                          word.lower() in list_word]
    for i in space_words_newline_clean_rn_final:

        jsdata = jsdata.replace(' ' + re.escape(i) + "\r\n",
                                " " + '<span style="background-color:#65B4D7;">' + re.escape(i) + '</span>' + "\r\n",
                                re.IGNORECASE)

    # Checking for the words preceded by newline snd followed by special character
    newline_word_special_character = re.findall(r'[\r\n]*[A-Za-z0-9]*[!@#$%^&*()+={}\':"\\|;,.<>/?]*', jsdata, re.I)
    newline_word_special_character_clean = [ele.strip() for ele in newline_word_special_character]
    newline_word_special_character_clean = [re.sub(r'[\n\r\t<()!@#$%^&*+={}\':"\\|;,.>/?\s]', '', c) for c in
                                            newline_word_special_character_clean]
    newline_word_special_character_clean_final = [word for word in newline_word_special_character_clean if
                                                  word.lower() in list_word]
    for i in newline_word_special_character_clean_final:
        for pat_end in pattern:
                pattern_to_find = '\r\n' + str(i) + str(pat_end)
                if pattern_to_find in jsdata:
                    jsdata = jsdata.replace('\r\n' + re.escape(i) + str(pat_end),
                                            '\r\n' + '<span style="background-color:#65B4D7;">' + re.escape(
                                                i) + '</span>' + str(pat_end),
                                            re.IGNORECASE)

    # Checking for the words preceded by space snd followed by special character
    space_word_special_character = re.findall(" "+r'[A-Za-z0-9]*[!@#$%^&*()+={}\':"\\|;,.<>/?]*', jsdata, re.I)
    space_word_special_character_clean = [ele.strip() for ele in space_word_special_character]
    space_word_special_character_clean = [re.sub(r'[\n\r\t<()!@#$%^&*+={}\':"\\|;,.>/?\s]', '', c) for c in
                                          space_word_special_character_clean]
    space_word_special_character_final = [word for word in space_word_special_character_clean if
                                          word.lower() in list_word]

    for i in space_word_special_character_final:
        for pat_end in pattern:
            pattern_to_find = ' ' + str(i) + str(pat_end)
            if pattern_to_find in jsdata:
                jsdata = jsdata.replace(' ' + re.escape(i) + str(pat_end),
                                        ' ' + '<span style="background-color:#65B4D7;">' + re.escape(
                                            i) + '</span>' + str(pat_end),
                                        re.IGNORECASE)

    # Checking for the words preceded by special character snd followed by \r\n
    special_character_word_rn = re.findall(r'[!@#$%^&*()+={}\':"\\|;,.<>/?]*[A-Za-z0-9]*[\r\n]*', jsdata, re.I)
    special_character_word_rn_clean = [ele.strip() for ele in special_character_word_rn]
    special_character_word_rn_clean = [re.sub(r'[\n\r\t<()!@#$%^&*+={}\':"\\|;,.>/?\s]', '', c) for c in
                                       special_character_word_rn_clean]
    special_character_word_rn_final = [word for word in special_character_word_rn_clean if
                                       word.lower() in list_word]

    for i in special_character_word_rn_final:
        for pat_start in pattern:
            pattern_to_find = str(pat_start) + str(i) + '\r\n'
            if pattern_to_find in jsdata:
                jsdata = jsdata.replace(str(pat_start) + re.escape(i) + '\r\n',
                                        str(pat_start) + '<span style="background-color:#65B4D7;">' + re.escape(
                                            i) + '</span>' + '\r\n',
                                        re.IGNORECASE)

    # checking for word preceded special_character snd followed by \n
    special_character_word_n = re.findall(r'[!@#$%^&*()+={}\':"\\|;,.<>/?]*[A-Za-z0-9]*\n*', jsdata, re.I)
    special_character_word_n_clean = [ele.strip() for ele in special_character_word_n]
    special_character_word_n_clean = [re.sub(r'[\n\r\t<()!@#$%^&*+={}\':"\\|;,.>/?\s]', '', c) for c in
                                      special_character_word_n_clean]
    special_character_word_n_final = [word for word in special_character_word_n_clean if
                                      word.lower() in list_word]
    for i in special_character_word_n_final:
        for pat_start in pattern:
            pattern_to_find = str(pat_start) + str(i) + '\n'
            if pattern_to_find in jsdata:
                jsdata = jsdata.replace(str(pat_start) + re.escape(i) + '\n',
                                        str(pat_start) + '<span style="background-color:#65B4D7;">' + re.escape(
                                            i) + '</span>' + '\n',
                                        re.IGNORECASE)

    # Checking single word in a line
    single_word = re.findall(r'[\r\n]*[A-Za-z0-9]*[\r\n]*', jsdata, re.I)
    single_word = [ele.strip() for ele in single_word]
    single_word_clean = [re.sub(r'[\n\r\t<()!@#$%^&*+={}\':"\\|;,.>/?\s]', '', c) for c in single_word]
    single_word_final = [word for word in single_word_clean if word.lower() in list_word]
    for i in single_word_final:
        jsdata = jsdata.replace('\r\n' + re.escape(i) + "\r\n",
                                "\r\n" + '<span style="background-color:#65B4D7;">' + re.escape(i) + '</span>' + "\r\n",
                                re.IGNORECASE)

    # Replacing special character in processed jsdata
    jsdata = jsdata.replace("�", "'")
    jsdata = jsdata.replace("\r\n", "<br>")
    global total_word_found
    total_word_found = highlight_data + [first_word] + last_words_fullstop + words_to_highlight_first_word +\
        words_to_highlight_first_word_preceded_newline + word_followed_by_special_character_final +\
        space_words_newline_clean_final + space_words_newline_clean_rn_final +\
        newline_word_special_character_clean_final + space_word_special_character_final + \
        special_character_word_rn_final + special_character_word_n_final + single_word_final + \
        words_to_highlight_fullstop
    total_word_found_inter = list(set([w.lower() for w in total_word_found]))
    total_word_found_inter = [w for w in total_word_found_inter if w.lower() in list_word]
    list_text_set = set(list_text)
    total_word_found_set = set(total_word_found_inter)
    total_word_found = list_text_set & total_word_found_set
    total_word_found = list(total_word_found)
    return jsdata
    # return render_template("trial_output.html", file_data=str(temp_data))


def design_table(dict_input):
    """
    Design the table to render in result html
    :param dict_input:
    :return:
    """
    table_string = ""
    for (key, value) in dict_input.items():
        table_string += '''   
        <tr>
        <td>{0}</td>
        <td>{1}</td>
        <td>{2}</td>
        </tr>
        '''.format(key, ":", value)
    return table_string


if __name__ == "__main__":
	app.run(host='0.0.0.0',debug=True)

