import { useState, ChangeEvent } from 'react';
import reactLogo from './assets/react.svg';
import viteLogo from '/vite.svg';
import './App.css';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [inputQuestion, setInputQuestion] = useState('');
  const [filePath, setFilePath] = useState<string>('');
  const [displayedQuestion, setDisplayedQuestion] = useState<string>('');
  const [context, setContext] = useState<string[]>([]);
  const [answer, setAnswer] = useState<string>('');
  const [expandedContextIndex, setExpandedContextIndex] = useState<number | null>(null);

  // Handle input change for the question
  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    setInputQuestion(e.target.value);
  };

  // Handle file change and upload the selected file
  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      console.log(file);

      // Create form data and append the selected file
      const formData = new FormData();
      formData.append('file', selectedFile);

      try {
        const uploadResponse = await fetch('http://localhost:8000/upload', {
          method: 'POST',
          body: formData,
        });

        if (uploadResponse.ok) {
          const uploadData = await uploadResponse.json();
          console.log('File uploaded successfully:', uploadData);
          setFilePath(uploadData.filePath);
        } else {
          console.error('Failed to upload file:', uploadResponse.statusText);
        }
      } catch (error) {
        console.error('Error uploading file:', error);
      }
    }
  };

  // Handle question submission
  const handleQuestionSubmit = async () => {
    if (!filePath) {
      alert("Please upload a file first.");
      return;
    }
    if (!inputQuestion) {
      alert("Please enter a question.");
      return;
    }

    try {
      setDisplayedQuestion(inputQuestion);
      setContext([]);
      setAnswer('');
      setInputQuestion('');

      const retrieveResponse = await fetch(`http://localhost:8000/retrieve_from_path?file_path=${encodeURIComponent(filePath)}&question=${encodeURIComponent(inputQuestion)}`);

      if (retrieveResponse.ok) {
        const reader = retrieveResponse.body?.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader?.read() || {};
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          let boundary = buffer.indexOf('\n');
          while (boundary !== -1) {
            const line = buffer.substring(0, boundary).trim();
            buffer = buffer.substring(boundary + 1);

            if (line) {
              try {
                const data = JSON.parse(line);
                if (data.context) {
                  setContext(data.context);
                }
                if (data.answer) {
                  setAnswer(prev => (prev ? `${prev} ${data.answer}` : data.answer));
                }
              } catch (e) {
                console.error('Error parsing streamed data:', e);
              }
            }
            boundary = buffer.indexOf('\n');
          }
        }
      } else {
        console.error('Failed to retrieve:', retrieveResponse.statusText);
      }
    } catch (error) {
      console.error('Error retrieving answer:', error);
    }
  };

  // Toggle context display
  const toggleContext = (index: number) => {
    setExpandedContextIndex(expandedContextIndex === index ? null : index);
  };

  return (
    <div className="container">
      <div className="header">
        <a href="https://vitejs.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <input type="file" onChange={handleFileChange} />
        <p>
          Edit <code>frontend/src/App.tsx</code> and <code>backend/app/main.py</code> to customize.
        </p>
      </div>
      <div className="question-form">
        {displayedQuestion && (
          <div className="displayed-question">
            <h2>Question:</h2>
            <p>{displayedQuestion}</p>
          </div>
        )}
        {context.length > 0 && (
          <div className="context-box">
            <div className="context-numbers">
              {context.map((_, index) => (
                <div
                  key={index}
                  className={`context-item ${expandedContextIndex === index ? 'expanded' : ''}`}
                  onClick={() => toggleContext(index)}
                >
                  <p><strong>Context {index + 1}</strong></p>
                </div>
              ))}
            </div>
            {expandedContextIndex !== null && (
              <div className="context-content">
                <p dangerouslySetInnerHTML={{ __html:context[expandedContextIndex]}}/>
              </div>
            )}
          </div>
        )}
        {answer && (
          <div className="answer-box">
            <h2>Answer:</h2>
            <p dangerouslySetInnerHTML={{ __html: answer }} />
          </div>
        )}
        <input
          type="text"
          placeholder="Enter your question"
          value={inputQuestion}
          onChange={handleInputChange}
        />
        <button onClick={handleQuestionSubmit}>Send</button>
      </div>

      <p className="read-the-docs">
        Click on the Vite and React logos to learn more.
      </p>
      <footer className="footer">
        <p>&copy; {new Date().getFullYear()}  {' '}
          <a href="https://hessian.ai/de/personen/perpetue-kuete-tiayo/" target="_blank">
             Perpetue Kuete Tiayo.
          </a> All Rights Reserved.</p> 
        <p>Let's connect on  {' '}
          <a href="https://www.linkedin.com/in/perpetue-k-375306185" target="_blank">
            LinkedIn
          </a>. 
        </p>
      </footer>
    </div>
  );
}

export default App;
