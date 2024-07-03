import { useState, ChangeEvent, FormEvent } from 'react';
import reactLogo from './assets/react.svg';
import viteLogo from '/vite.svg';
import './App.css';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [question, setQuestion] = useState('');
  const [filePath, setFilePath] = useState<string>('');
  const [displayedQuestion, setDisplayedQuestion] = useState<string>('');
  const [context, setContext] = useState<string[]>([]);
  const [answer, setAnswer] = useState<string>('');

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    setQuestion(e.target.value);
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) {
      alert("Please select a file to upload.");
      return;
    }
    const formData = new FormData();
    formData.append('file', file);

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
  };

  const handleQuestionSubmit = async () => {
    if (!filePath) {
      alert("Please upload a file first.");
      return;
    }
    if (!question) {
      alert("Please enter a question.");
      return;
    }

    try {
      setDisplayedQuestion(question);
      setContext([]);
      setAnswer('');

      const retrieveResponse = await fetch(`http://localhost:8000/retrieve_from_path?file_path=${encodeURIComponent(filePath)}&question=${encodeURIComponent(question)}`);

      if (retrieveResponse.ok) {
        const reader = retrieveResponse.body?.getReader();
        const decoder = new TextDecoder();
        let result = '';

        while (true) {
          const { done, value } = await reader?.read() || {};
          if (done) break;
          result += decoder.decode(value);

          // Parsing the streamed JSON data
          result.trim().split('\n').forEach((line) => {
            try {
              const data = JSON.parse(line);
              if (data.context) {
                setContext(prev => [...prev, ...data.context]);
              }
              if (data.answer) {
                setAnswer(prev => prev + ' ' + data.answer);
              }
            } catch (e) {
              console.error('Error parsing streamed data:', e);
            }
          });
        }

        console.log('Retrieve response:', result);
      } else {
        console.error('Failed to retrieve:', retrieveResponse.statusText);
      }
    } catch (error) {
      console.error('Error retrieving answer:', error);
    }
  };

  return (
    <>
      <div>
        <a href="https://vitejs.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <form onSubmit={handleSubmit}>
          <input type="file" onChange={handleFileChange} />
          <button type="submit">Upload File</button>
        </form>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
      {displayedQuestion && (
        <div className="displayed-question">
          <h2>Question:</h2>
          <p>{displayedQuestion}</p>
        </div>
      )}
      {context.length > 0 && (
        <div className="context-box">
          <h2>Context:</h2>
          {context.map((text, index) => (
            <p key={index}>{text}</p>
          ))}
        </div>
      )}
      {answer && (
        <div className="answer-box">
          <h2>Answer:</h2>
          <p>{answer}</p>
        </div>
      )}
      <div className="question-form">
        <input
          type="text"
          placeholder="Enter your question"
          value={question}
          onChange={handleInputChange}
        />
        <button onClick={handleQuestionSubmit}>Send</button>
      </div>
      
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  );
}

export default App;
