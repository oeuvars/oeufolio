"use client"

import React, { useState } from "react";
import { showToast } from "./show-toasts";
import { createClient } from "@supabase/supabase-js";

const Input = () => {
  const [enquiry, setEnquiry] = useState({
    email: "",
  });
  const [isValidEmail, setIsValidEmail] = useState(false);
  const supabase = createClient(
    "https://cwwohaipubnlygrkhunn.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3d29oYWlwdWJubHlncmtodW5uIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxNjU1NjEyNywiZXhwIjoyMDMyMTMyMTI3fQ.8r4GoxxN40a7RrVCiqDQn9OqYmBLO8MIRuhgNFHbDjk"
  );
  const handleClick = async () => {
    if (isValidEmail) {
      try {
        const { error } = await supabase.from("oeufolio").insert(enquiry);

        if (error) {
          showToast("Try again later", false);
        } else {
          showToast("Subscribed to the Oeuletter", true);
          setEnquiry({
            email: "",
          });
        }
      } catch (error) {
        console.error("Unexpected error:", error);
      }
    } else {
      showToast("Not a valid email", false);
    }
  };
  const handleEmailChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const inputEmail = event.target.value;
    setEnquiry({
      email: inputEmail,
    });

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    setIsValidEmail(emailRegex.test(inputEmail));
  };
  return (
    <div className="flex phone:w-[80vw] sm:w-auto phone:gap-2 lg:gap-0 mt-2">
      <input
        className={`bg-[#222222] text-[#FAFAFA] phone:px-3 lg:px-6 py-3 w-full rounded-md outline-none focus:outline-2 focus:outline focus:outline-[#333333] ${
          isValidEmail ? "" : "border-red-500"
        }`}
        placeholder="something@gmail.com"
        type="email"
        id="email"
        name="email"
        onChange={handleEmailChange}
        value={enquiry.email}
        required
      />
      <button className="phone:-ml-10 lg:-ml-10" onClick={handleClick}>
        <img src="/icons/arrow.svg" alt="" className="phone:size-5 lg:size-7 my-auto" />
      </button>
    </div>
  );
};

export default Input;