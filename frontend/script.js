function isCSVConvertible(text) {
  const lines = text.trim().split("\n");
  let validPairs = 0;

  for (const line of lines) {
    const cleanLine = line.replace(/^\*+\s*/, "").trim(); // remove leading *, spaces
    if (cleanLine.includes(":")) validPairs++;
  }

  return validPairs >= 3;
}

function isCSVConvertible(text) {
  const lines = text.trim().split("\n");
  let validPairs = 0;

  for (const line of lines) {
    const cleanLine = line.replace(/^\*+\s*/, "").trim(); // remove leading *, spaces
    if (cleanLine.includes(":")) validPairs++;
  }

  return validPairs >= 3; // allow only if 3+ valid pairs
}

function convertToCSV(text) {
  const lines = text.trim().split("\n");
  const rows = [];
  let section = "";

  for (const line of lines) {
    if (!line.trim()) continue;

    // Check if it's a section header like **Security Configuration:**
    const sectionMatch = line.trim().match(/^\*\*(.+)\*\*:?\s*$/);
    if (sectionMatch) {
      section = sectionMatch[1].trim();
      continue;
    }

    const cleanLine = line.replace(/^\*+\s*/, "").trim();
    const [key, ...rest] = cleanLine.split(":");
    if (key && rest.length) {
      let field = key.trim();
      let value = rest.join(":").trim();

      // Ensure the key is not empty
      if (!field) continue;

      // Sanitize both field and value to prevent Excel formula injection
      if (/^[=+\-@]/.test(field)) field = `'${field}`;
      if (/^[=+\-@]/.test(value)) value = `'${value}`;

      // Prefix with section
      field = section ? `${section} - ${field}` : field;

      // Wrap fields in quotes to avoid Excel confusion
      rows.push([`"${field}"`, `"${value}"`]);
    }
  }

  let csv = `"Field","Value"\n`;
  csv += rows.map(row => row.join(",")).join("\n");
  return csv;
}


function downloadCSV(csv, filename = "response.csv") {
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();

  URL.revokeObjectURL(url);
}


async function sendQuery() {
  const question = document.getElementById("query").value;

  const response = await fetch("http://localhost:5000/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  const data = await response.json();
  const responseBox = document.getElementById("response");
  const csvBtn = document.getElementById("csvBtn");


  const answer = data.answer || "Error retrieving answer"; 
  responseBox.innerText = answer;


  // Allow DOM to update before checking scrollHeight
  setTimeout(() => {
    const container = document.getElementById("response-container");

    // Show scroll button only if content overflows
    if (container.scrollHeight > container.clientHeight + 20) {
      scrollBtn.style.display = "block";
    } else {
      scrollBtn.style.display = "none";
    }
  }, 100);

if (isCSVConvertible(answer)) {
    csvBtn.style.display = "inline-block";
    csvBtn.onclick = () => {
      const csv = convertToCSV(answer);
      downloadCSV(csv);
    };
  } else {
    csvBtn.style.display = "none";
  }
}
