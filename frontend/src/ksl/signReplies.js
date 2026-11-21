/** English taps for each real signed line. Care words keep their engine ids. */

export const SIGN_ORDER = [
  "--8pSDeC-fg_0-5",
  "--8pSDeC-fg_1-5",
  "1xKU91ggLeI_2-5",
  "--8pSDeC-fg_7-5",
  "06jk1stVwMI_2-5",
  "CE23zzfUBDw_7-5",
  "cQBrXCcfDyc_22-5",
  "Cu1rDgWOZ9w_15-8",
  "5dodEz2r56M_16-8",
  "-0N0jbyBW6g_11-5",
  "-F6vN4bOBWs_16-8",
];

const okay = { id: "better", label: "I'm okay" };
const pain = { id: "worse", label: "I'm in extreme pain" };
const help = { id: "need help", label: "I need help" };
const thanks = { id: "thank you", label: "Thank you" };

export const SIGN_REPLIES = {
  "--8pSDeC-fg_0-5": [
    { id: "hello", label: "Hello" },
    { id: "i'm here", label: "Hi, I'm here" },
  ],
  "--8pSDeC-fg_1-5": [
    { id: "hello", label: "Hello" },
    { id: "nice to meet you", label: "Nice to meet you" },
  ],
  "1xKU91ggLeI_2-5": [okay, { id: "same", label: "About the same" }, pain],
  "--8pSDeC-fg_7-5": [okay, help, pain],
  "06jk1stVwMI_2-5": [okay, pain, help],
  "CE23zzfUBDw_7-5": [okay, pain, help],
  "cQBrXCcfDyc_22-5": [okay, { id: "not_yet", label: "Not yet" }, help],
  "Cu1rDgWOZ9w_15-8": [thanks, help],
  "5dodEz2r56M_16-8": [thanks, { id: "goodbye", label: "Goodbye" }],
  "-0N0jbyBW6g_11-5": [{ id: "you're welcome", label: "You're welcome" }, thanks],
  "-F6vN4bOBWs_16-8": [{ id: "goodbye", label: "Goodbye" }, thanks],
};
