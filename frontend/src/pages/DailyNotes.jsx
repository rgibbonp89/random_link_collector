import React, { useEffect, useState } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";
import ReactPaginate from "react-paginate";

function DailyNotes() {
  const [jsonData, setJsonData] = useState([]);
  const [page, setPage] = useState(0);
  const [minimizedBoxes, setMinimizedBoxes] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [editDailyNote, setDailyNoteIsEdited] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const fetchDailyNotesData = () => {
    const queryParams = `?timestamp=${new Date().getTime()}`;
    fetch(`/getalldailynotes${queryParams}`)
      .then((response) => response.json())
      .then((data) => {
        setJsonData(data);
        setMinimizedBoxes(data.map((item) => item.date_input));
      })
      .catch((error) => console.error(error));
  };
  useEffect(() => {
    fetchDailyNotesData();
  }, []);

  const handleEditDailyNote = (event, item) => {
    setIsLoading(true);
    event.preventDefault();
    const updatedDailyNote = {
      id: item.id,
      daily_note_text: event.target.elements.dailyNoteText.value,
    };
    fetch(`/updatedailynote`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updatedDailyNote),
    })
      .then((response) => response.json())
      .then(() => {
        setIsLoading(false);
        setIsSubmitted(true);
      })
      .then((data) => {
        setJsonData((prevData) =>
          prevData.map((d) =>
            d.id === item.id ? { ...d, ...updatedDailyNote } : d
          )
        );
      })
      .catch((error) => console.error(error));
  };
  const handleDailyNoteBoxMinimize = (boxId) => {
    if (!minimizedBoxes.includes(boxId)) {
      setMinimizedBoxes([...minimizedBoxes, boxId]);
    } else {
      setMinimizedBoxes(minimizedBoxes.filter((id) => id !== boxId));
    }
  };

  const itemsPerPage = 10;
  const offset = page * itemsPerPage;
  const filteredData = jsonData.filter((item) => {
    return item.daily_note_text
      .toLowerCase()
      .includes(searchQuery.toLowerCase()); // fallback for invalid readStatusFilter values
  });
  const pageCount = filteredData
    ? Math.ceil(filteredData.length / itemsPerPage)
    : 0;
  const currentPageData = filteredData.slice(offset, offset + itemsPerPage);

  const handlePageClick = (selectedPage) => {
    setPage(selectedPage.selected);
  };

  const createNewDailyNote = () => {
    const queryParams = `?timestamp=${new Date().getTime()}`;
    fetch(`/createnewdailynote${queryParams}`)
      .then((response) => response.json())
      .catch((error) => console.error(error));
  };

  return (
    <div className="App">
      <header className="App-header">
        <p>Daily notes</p>
      </header>
      <header className="App"></header>
      <input
        className={"search-bar"}
        type="text"
        placeholder="Search articles..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />
      <button
          className={'button'}
          style={{marginLeft:50}}
          onClick={() => createNewDailyNote()}
      >Create new daily note</button>
      {currentPageData.map((item) => (
        <div
          key={item.date_input}
          className={`box
               ${
                 minimizedBoxes.includes(item.date_input)
                   ? "box--minimized"
                   : ""
               }`}
        >
            <h2>{item.date_input}</h2>
          <button
            className={"button"}
            onClick={() => handleDailyNoteBoxMinimize(item.date_input)}
          >
            Expand
          </button>
          {editDailyNote !== item && (
            <button
              className={"button"}
              onClick={() => setDailyNoteIsEdited(item)}
              style={{
                display: minimizedBoxes.includes(item.date_input)
                  ? "none"
                  : "block",
              }}
            >
              Edit
            </button>
          )}
          {editDailyNote === item && (
            <form onSubmit={(event) => handleEditDailyNote(event, item)}>
              <textarea
                className={"textarea"}
                type="text"
                name="dailyNoteText"
                defaultValue={item.daily_note_text}
                style={{ padding: "10px", marginBottom: "10px" }}
              />
              <button className={"button"} type="submit">
                Submit
              </button>
              {isLoading && <p>Loading...</p>}
              {isSubmitted && <p>Daily note edit made successfully!</p>}
              <button
                className={"button"}
                type="button"
                onClick={() => setDailyNoteIsEdited(null)}
              >
                Cancel
              </button>
            </form>
          )}
          {!minimizedBoxes.includes(item.date_input) && (
            <>
              <p className="subheader"> Notes:</p>
              <ReactMarkdown>{item.daily_note_text}</ReactMarkdown>
            </>
          )}
        </div>
      ))}
      <ReactPaginate
        pageCount={pageCount}
        onPageChange={handlePageClick}
        containerClassName={"pagination"}
        pageLinkClassName={"page-link"}
        previousLinkClassName={"page-link"}
        nextLinkClassName={"page-link"}
        disabledClassName={"disabled"}
        activeClassName={"active"}
        pageRangeDisplayed={5}
        marginPagesDisplayed={2}
        pageLinkStyle={{ listStyleType: "none" }}
      />
    </div>
  );
}
export default DailyNotes;
