import tiktoken

GPT_MODEL = "gpt-3.5-turbo"  # only matters insofar as it selects which tokenizer to use

def num_tokens(text: str, model: str = GPT_MODEL) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def halved_by_delimiter(string: str, delimiter: str = "\n") -> list[str, str]:
    """Split a string in two, on a delimiter, trying to balance tokens on each side."""
    chunks = string.split(delimiter)
    if len(chunks) == 1:
        return [string, ""]  # no delimiter found
    elif len(chunks) == 2:
        return chunks  # no need to search for halfway point
    else:
        total_tokens = num_tokens(string)
        halfway = total_tokens // 2
        best_diff = halfway
        for i, chunk in enumerate(chunks):
            left = delimiter.join(chunks[: i + 1])
            left_tokens = num_tokens(left)
            diff = abs(halfway - left_tokens)
            if diff >= best_diff:
                break
            else:
                best_diff = diff
        left = delimiter.join(chunks[:i])
        right = delimiter.join(chunks[i:])
        return [left, right]


def truncated_string(
    string: str,
    model: str,
    max_tokens: int,
    print_warning: bool = True,
) -> str:
    """Truncate a string to a maximum number of tokens."""
    encoding = tiktoken.encoding_for_model(model)
    encoded_string = encoding.encode(string)
    truncated_string = encoding.decode(encoded_string[:max_tokens])
    if print_warning and len(encoded_string) > max_tokens:
        print(f"Warning: Truncated string from {len(encoded_string)} tokens to {max_tokens} tokens.")
    return truncated_string


def split_strings_from_subsection(
    subsection: tuple[list[str], str],
    max_tokens: int = 1000,
    model: str = GPT_MODEL,
    max_recursion: int = 5,
) -> list[str]:
    """
    Split a subsection into a list of subsections, each with no more than max_tokens.
    Each subsection is a tuple of parent titles [H1, H2, ...] and text (str).
    """
    titles, text = subsection
    string = "\n\n".join(titles + [text])
    num_tokens_in_string = num_tokens(string)
    # if length is fine, return string
    if num_tokens_in_string <= max_tokens:
        return [string]
    # if recursion hasn't found a split after X iterations, just truncate
    elif max_recursion == 0:
        return [truncated_string(string, model=model, max_tokens=max_tokens)]
    # otherwise, split in half and recurse
    else:
        titles, text = subsection
        for delimiter in ["\n\n", "\n", ". "]:
            left, right = halved_by_delimiter(text, delimiter=delimiter)
            if left == "" or right == "":
                # if either half is empty, retry with a more fine-grained delimiter
                continue
            else:
                # recurse on each half
                results = []
                for half in [left, right]:
                    half_subsection = (titles, half)
                    half_strings = split_strings_from_subsection(
                        half_subsection,
                        max_tokens=max_tokens,
                        model=model,
                        max_recursion=max_recursion - 1,
                    )
                    results.extend(half_strings)
                return results
    # otherwise no split was found, so just truncate (should be very rare)
    return [truncated_string(string, model=model, max_tokens=max_tokens)]

def split_into_sections(file_name: str) -> [tuple[str, [str]]]:
    file = open(file_name, "r")
    res, tmp, active, match_tok = [], None, False, 0
    
    for line in file.readlines():
        if line.strip().isnumeric() and int(line) == match_tok+1:
            if tmp:
                res.append((str(match_tok), tmp))
            
            match_tok += 1
            active = True
            tmp = []
            continue
        
        if active:
            tmp.append(line)
            
    file.close()
            
    return res

def save_sections_to_new_files(sections: [tuple[str, [str]]]) -> None:
    """
    Writes extracted sections to new individual text files for easier future processing
    """
    for title, text in sections:
        f = open(f"db/{title}.txt", "w")
        for line in text:
            f.write(line)

def parse_and_join_ans(ans: [str]) -> str:
    ans = [tok for tok in ans if tok not in ['\n', '\t', '\u2003\n']]
    return ''.join(ans)

def split_into_qa_pairs(sections: [tuple[str, [str]]]) -> [tuple[[str], str]]:
    """
    """
    res, questions, ans = [], [], []
    for section, text in sections:
        tmp = []
        for line in text:
            if line.startswith("<Q>"):
                if len(ans) > 0:
                    p_ans = parse_and_join_ans(ans)
                    tmp.append((questions, p_ans))
                    questions = []
                    ans = []
                
                questions.append(line[4:])
                continue
            
            ans.append(line)
            
        if len(ans) > 0:
            p_ans = parse_and_join_ans(ans)
            tmp.append((questions, p_ans))
            
        res.append((section, tmp))
        
    return res