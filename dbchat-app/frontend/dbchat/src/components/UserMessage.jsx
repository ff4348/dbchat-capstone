import React from "react";

export default function UserMessage({ query, user_friendly, csv_download_link}) {
  console.log("UserMessage component loaded...")
  console.log("UserMessage:",user_friendly)
  console.log("Additional attributes NOT used:",query,csv_download_link)
  return (
    <div className="message-container">
      <div className="user-message">{user_friendly}</div>
    </div>
  );
}
