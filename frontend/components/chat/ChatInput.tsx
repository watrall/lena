import { KeyboardEventHandler, RefObject } from 'react';

type Props = {
    input: string;
    setInput: (value: string) => void;
    onSubmit: () => void;
    loading: boolean;
    disabled: boolean;
    inputRef: RefObject<HTMLTextAreaElement>;
    placeholder: string;
};

export const ChatInput = ({
    input,
    setInput,
    onSubmit,
    loading,
    disabled,
    inputRef,
    placeholder,
}: Props) => {
    const handleKeyDown: KeyboardEventHandler<HTMLTextAreaElement> = (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            onSubmit();
        }
    };

    const canSend = !disabled && input.trim().length > 0 && !loading;

    return (
        <div className="flex flex-col gap-3 md:flex-row md:items-end">
            <label className="flex-1">
                <span className="sr-only">Ask a question</span>
                <textarea
                    ref={inputRef}
                    value={input}
                    onChange={(event) => setInput(event.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    rows={3}
                    className="lena-textarea"
                    disabled={disabled || loading}
                />
            </label>
            <div className="flex items-center gap-3">
                <button
                    type="button"
                    onClick={onSubmit}
                    disabled={!canSend}
                    className="lena-button-primary px-6 py-3 text-sm"
                >
                    {loading ? 'Sending…' : 'Send'}
                </button>
            </div>
        </div>
    );
};
