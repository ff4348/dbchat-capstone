import React, { useEffect, useRef } from "react";

export default function Messages({ messages }) {
  console.log("Messages component loaded...")
  console.log("Messages received:",messages)
  const el = useRef(null);
  useEffect(() => {
    console.log("Messages scroll hook loaded...")
    el.current.scrollIntoView({ block: "end", behavior: "smooth" });
  });
  return (
    <div className="messages">
      {messages}
      <div id={"el"} ref={el} />
    </div>
  );
}
