import React, { useState } from 'react';
import './App.css';



function Submit() {
  const [formData, setFormData] = useState({
      name_input: 'Missing name!',
      url_input: '',
      my_summary: null,
  });

  const handleInputChange = (event) => {
    const { name, value } = event.target;


    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    fetch('/submit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log('Success:', data);
        // do something with the response data
      })
      .catch((error) => {
        console.error('Error:', error);
        // handle the error
      });
  };

  return (
      <div className="app">
        <header className="box">
    <form className={'form'} onSubmit={handleSubmit}>
      <label className={'label'}>
        Name:
        <input className={'input'} type="text" name="name_input" onChange={handleInputChange} />
      </label>
      <label className={'label'}>
        URL:
        <input className={'input'} type="text" name="url_input" onChange={handleInputChange} />
      </label>
      <label className={'label'}>
        My summary:
        <textarea className={'textarea'}  type="text" name="my_summary" onChange={handleInputChange} />
      </label >
      <button className={'button'} type="submit">Submit</button>
    </form>
          </header>
      </div>

  );
}

export default Submit;
