class LlmManager():
    def __init__(self):
        try:
            use_gemini, self.client = self.start_gemini() # prefer gemini, but if that doesn't work default to ollama mistral
        except Exception as e:
            #print(e, type(e))
            print("Cannot use Gemini right now. If you haven't configured .env.secret, put your API key there.")
            print(f'Gemini reported error: {e}')
            use_gemini = False
        if use_gemini:
            self.model = 'gemini'
        else:
            self.model = 'ollama'
        self.gemini_model = 'gemini-2.0-flash'
        self.ollama_model = 'mistral'
        self.system = 'You are a master python programmer. \
    Your job is to respond to queries about python \
    program design and syntax in an efficient and direct \
    manner. Be sure that each output leads with specific, \
    correct, and modern python code. Be sure to give pointers \
    about more effective strategies when necessary, though your \
    primary intent should be to answer the question posed instead \
    of to improve the strategy. In addition to valid python code \
    suggestions, you may also include some reasoning. However, keep \
    non-coding responses to a minimal length. Responses that are not \
    code should be exclusively after all code, and should last for no \
    more than 200 tokens, unless more are absolutely necessary.'
        self.ollama_system = { # configure to ollama format ahead of time
            "role": "system", 
            "content": self.system}
        self.history = []
        self.context_length = len(self.system) // 4
        self.max_context_length = 7500 # keep context reasonable. gemini 2.0 flash supports max 30k, but I don't want to deal with that much
        self.ollama_started = False # flag to monitor whether WSL was started from this instance of the LlmManager

    def prompt(self,query,system=None):
        '''
        Override system prompt if necessary (this will cause a bug if passing a system prompt to each call of llm_manager.prompt)
        '''
        if system != None:
            self.system += system
        if self.model == 'gemini': # determine correct model and prompt it
            result = self.prompt_gemini(query)
        elif self.model == 'ollama':
            result = self.prompt_ollama(query)
        else: # catch edge cases
            result = f"Something's wrong here. I'm supposed to use 'ollama' or 'gemini', but I got '{self.model}'. Correct & try again."
        return result

    def prompt_gemini(self,query):
        '''
        Prompt Google Gemini for a response using history.
        '''
        from google import genai
        self.history.append(query) # keep track of the history
        self.context_length += len(query) # make sure the context window is reasonable
        while self.context_length > self.max_context_length:
            self.context_length -= len(self.history[0])
            self.history[0].pop() # kill some history if needed
        system_prompt = self.system # this is just here because in another instance I pass some gemini-specific instructions
        config = genai.types.GenerateContentConfig(candidate_count=1, system_instruction=system_prompt)
        query = '\n'.join(self.history) # set up the whole context window
        response = self.client.models.generate_content(model=self.gemini_model, config=config, contents=query).text.strip() # query and get just the text. I really don't care about the rest right now
        print(response)
        self.history.append(response) # put the response in 
        return response

    def start_gemini(self):
        '''
        Set up a gemini client if one can be created. This will give an error if the response isn't ok, which is handled in __init__.
        '''
        from google import genai
        import os
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        response = client.models.generate_content(model="gemini-2.0-flash", contents="Reply with 1 word so I know the connection is working.").text # not sure how you're supposed to check if a connection is live, but this is easy and it works.
        if len(response) > 0:
            return True, client # give us a gemini client to use
        return False, None

    def prompt_ollama(self,query):
        '''
        Alternatively, use ollama to query. I'm not going to comment this because it's kind of awkward and annoying.
        This also doesn't work unless you've separately configured ollama *and* have launched WSL as a separate process. 
        You don't have to keep WSL open, but you do have to start it separately.
        start_ollama_server doesn't currently work, and I'm not sure why.
        '''
        import ollama
        prompt = {'role': 'user',
                  'content': query}
        messages = [self.ollama_system]
        if len(self.history) > 0:
            messages.append(self.history)
        messages.append(prompt)
        #print(messages)
        try:
            output = ollama.chat(model=self.ollama_model, messages=messages)
        except ConnectionError:
            self.start_ollama_server()
            output = ollama.chat(model=self.ollama_model, messages=messages)
        response = output['message']['content']
        self.history.append(response)
        return response

    def start_ollama_server(self):
        '''
        Try to start the ollama server. This expects the ollama windows distribution to be installed and expects the ollama install directory in .env.secret
        '''
        import subprocess, time, ollama
        from os import path,environ
        file = path.join(path.dirname(__file__),'start_ollama.bat')
        for _ in range(5):
            print(f'Not connected to Ollama. Attempting manual server start {_+1} of 5.')
            try:
                subprocess.run([file, environ.get("OLLAMA_DIR")])
                print('Trying open Ollama')
                time.sleep(5)
                print('Testing whether Ollama is running.')
                try:
                    ollama.ps()
                    print('Everything ok. Returning to original process.')
                    self.ollama_started = True
                    return
                except Exception as e:
                    print(e,type(e))
            except ConnectionError as e:
                pass
        print('Unknown error. Cannot start Ollama server.')

    def close_ollama_server(self):
        import subprocess, time
        from os import path
        file = path.join(path.dirname(__file__),'close_ollama.bat')
        subprocess.run([file],shell=True)
        time.sleep(2)

if __name__ == '__main__':
    # Context managers that extend common packages to make things slightly ~pretty~ or to kill annoying print output.
    from env_manager import load_dotenv
    from wrap_to_console import wrap
    from quash_print_output import quash_print_output as quash
    from markdown_printer import MarkdownPrinter as mark

    intro_header = '''
# LLM Python Syntax Guide

## By Zach Stichter

##### Available under MIT license

Enter queries as needed. Type `exit` to quit.'''

    with mark():
        print(intro_header)

    load_dotenv()
    mgr = LlmManager()


    while True:
        prompt = input('[Interactive Python Docs]: ')
        if prompt == 'exit':
            break
        with wrap():
            with quash():
                result = mgr.prompt(prompt)
            with mark():
                print(f'{result}\n')

exit_string = '''LLM Python Syntax Guide

Copyright (c) 2025 Zachary Stichter

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''

print(exit_string)
with quash():
    if mgr.ollama_started:
        mgr.close_ollama_server()
input('Press enter to exit')

