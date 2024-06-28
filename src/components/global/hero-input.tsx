"use client";

import React, { useState } from "react";
import { showToast } from "./show-toasts";

const Input = () => {
  const [enquiry, setEnquiry] = useState({
    email: "",
  });
  const [isValidEmail, setIsValidEmail] = useState(false);

  const handleClick = async (e: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    e.preventDefault();
    if (isValidEmail) {
      try {
        const form = document.getElementById("email-form") as HTMLFormElement;
        const formData = new FormData(form);

        await fetch(form.action, {
          method: "POST",
          body: formData,
          mode: "no-cors",
        });

        showToast("Subscribed to the Oeuletter", true);
        setEnquiry({
          email: "",
        });
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
    <form
      id="email-form"
      action="https://docs.google.com/forms/d/e/1FAIpQLSc7cz3tltdCuYy1J8DJA1al7mqDz62_AkMFzgs95Sg5Yn9dmA/formResponse"
      className="flex phone:w-[80vw] sm:w-auto phone:gap-2 lg:gap-0 mt-2"
    >
      <input
        className={`bg-[#222222] text-[#FAFAFA] phone:px-3 lg:px-6 py-3 w-full rounded-md outline-none focus:outline-2 focus:outline focus:outline-[#333333] ${
          isValidEmail ? "" : "border-red-500"
        }`}
        placeholder="something@gmail.com"
        type="email"
        id="email"
        name="entry.254229081"
        onChange={handleEmailChange}
        value={enquiry.email}
        required
      />
      <button className="phone:-ml-10 lg:-ml-10" onClick={handleClick}>
        <img src="/icons/arrow.svg" alt="" className="phone:size-5 lg:size-7 my-auto" />
      </button>
    </form>
  );
};

export default Input;
