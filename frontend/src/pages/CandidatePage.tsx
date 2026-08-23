import { type FormEvent, type ReactNode, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import { EditorialNote } from '../components/EditorialNote';
import { InternalHero } from '../components/InternalHero';
import { Section } from '../components/Section';
import { CandidateApiError, submitCandidateApplication } from '../candidate/candidateApi';
import { candidateFormEnabled } from '../candidate/candidateConfig';

const FIELD_CLASS =
  'w-full border border-brand-gray10/40 bg-white px-4 py-3 text-base text-brand-ink outline-none transition focus:border-brand-red disabled:cursor-not-allowed disabled:bg-brand-paperAlt/60';
const TEXTAREA_CLASS = `${FIELD_CLASS} min-h-36 resize-y`;
const HELP_CLASS = 'text-sm leading-6 text-brand-ink/65';
const STATUS_SUCCESS_CLASS = 'border-brand-gray10/20 bg-white/80 text-brand-ink';
const STATUS_ERROR_CLASS = 'border-brand-red/25 bg-white text-brand-red';
const INACTIVE_COPY = 'Приём заявок через сайт временно недоступен.';
const ACTIVE_COPY = 'Форма предназначена для отправки анкеты и фотографии в ДЛ «Астрея» №3. Фотография обрабатывается приватно и не публикуется.';
const SUCCESS_COPY = 'Заявка принята. Благодарим за обращение.';
const NETWORK_COPY = 'Не удалось отправить заявку. Проверьте соединение и попробуйте ещё раз.';
const VALIDATION_COPY = 'Проверьте заполнение анкеты и выбранную фотографию.';
const TOO_LARGE_COPY = 'Файл или запрос слишком большой.';
const TOO_MANY_COPY = 'Слишком много попыток отправки. Попробуйте позже.';
const TEMPORARY_COPY = 'Отправка заявки временно недоступна. Попробуйте позже.';
const UNAVAILABLE_COPY = 'Отправка заявок временно недоступна.';
const ST_PETERSBURG_COPY = 'Я понимаю, что подаю заявку на вступление в ложу, работающую в Санкт-Петербурге';

export function CandidatePage() {
  const formLock = useRef(false);
  const [submissionState, setSubmissionState] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');
  const [feedback, setFeedback] = useState<string | null>(null);
  const active = candidateFormEnabled;
  const disabled = !active || submissionState === 'submitting';
  const heroLead = active ? ACTIVE_COPY : INACTIVE_COPY;

  function clearFeedback() {
    if (submissionState !== 'idle') {
      setSubmissionState('idle');
      setFeedback(null);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!active || formLock.current) {
      return;
    }

    const form = event.currentTarget;
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    formLock.current = true;
    setSubmissionState('submitting');
    setFeedback('Отправка…');

    try {
      const response = await submitCandidateApplication(new FormData(form));
      if (!response.accepted) {
        throw new CandidateApiError(503);
      }
      form.reset();
      setSubmissionState('success');
      setFeedback(SUCCESS_COPY);
    } catch (error) {
      setSubmissionState('error');
      setFeedback(formatCandidateSubmissionError(error));
    } finally {
      formLock.current = false;
    }
  }

  return (
    <>
      <InternalHero eyebrow="Кандидату" title="Вступление" lead={heroLead} />
      <Section>
        <div className="mx-auto max-w-5xl space-y-8">
          <EditorialNote title={active ? 'Подача заявки' : 'Приём заявок'}>
            {active ? ACTIVE_COPY : INACTIVE_COPY}
          </EditorialNote>

          <form className="space-y-10" onInput={clearFeedback} onSubmit={handleSubmit}>
            <div className="absolute left-[-10000px] top-auto h-px w-px overflow-hidden">
              <label htmlFor="website" className="sr-only">
                Website
              </label>
              <input
                id="website"
                name="website"
                type="text"
                autoComplete="off"
                tabIndex={-1}
                disabled={disabled}
                aria-hidden="true"
                className={FIELD_CLASS}
              />
            </div>

            <fieldset
              disabled={disabled}
              className="rounded-3xl border border-brand-gray10/20 bg-white/75 p-6 shadow-formal lg:p-8"
            >
              <legend className="px-3 font-display text-3xl text-brand-ink">Анкета кандидата</legend>
              <div className="mt-8 grid gap-6 lg:grid-cols-2">
                <FormField id="full_name" label="Фамилия, имя, отчество" required className="lg:col-span-2">
                  <input
                    id="full_name"
                    name="full_name"
                    type="text"
                    required
                    maxLength={255}
                    autoComplete="name"
                    className={FIELD_CLASS}
                  />
                </FormField>

                <FormField id="date_of_birth" label="Дата рождения" required>
                  <input
                    id="date_of_birth"
                    name="date_of_birth"
                    type="date"
                    required
                    className={FIELD_CLASS}
                  />
                </FormField>

                <FormField id="city" label="Город проживания" required>
                  <input
                    id="city"
                    name="city"
                    type="text"
                    required
                    maxLength={120}
                    autoComplete="address-level2"
                    className={FIELD_CLASS}
                  />
                </FormField>

                <FormField id="phone" label="Телефон" required>
                  <input
                    id="phone"
                    name="phone"
                    type="tel"
                    required
                    maxLength={80}
                    autoComplete="tel"
                    className={FIELD_CLASS}
                  />
                </FormField>

                <FormField id="email" label="Email" required>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    maxLength={255}
                    autoComplete="email"
                    className={FIELD_CLASS}
                  />
                </FormField>

                <FormField id="education" label="Образование" required className="lg:col-span-2">
                  <textarea
                    id="education"
                    name="education"
                    required
                    maxLength={4000}
                    rows={4}
                    className={TEXTAREA_CLASS}
                  />
                </FormField>

                <FormField id="occupation" label="Работа / род занятий" required className="lg:col-span-2">
                  <textarea
                    id="occupation"
                    name="occupation"
                    required
                    maxLength={4000}
                    rows={4}
                    className={TEXTAREA_CLASS}
                  />
                </FormField>

                <FormField id="marital_status" label="Семейное положение" required>
                  <input
                    id="marital_status"
                    name="marital_status"
                    type="text"
                    required
                    maxLength={120}
                    className={FIELD_CLASS}
                  />
                </FormField>

                <FormField id="other_organizations" label="Членство в иных организациях" className="lg:col-span-2">
                  <textarea
                    id="other_organizations"
                    name="other_organizations"
                    maxLength={4000}
                    rows={4}
                    className={TEXTAREA_CLASS}
                  />
                </FormField>

                <FormField id="social_links" label="VK / публичные социальные ссылки" className="lg:col-span-2">
                  <textarea
                    id="social_links"
                    name="social_links"
                    maxLength={4000}
                    rows={4}
                    className={TEXTAREA_CLASS}
                  />
                </FormField>

                <FormField id="motivation" label="О себе / мотивация" required className="lg:col-span-2">
                  <textarea
                    id="motivation"
                    name="motivation"
                    required
                    maxLength={4000}
                    rows={7}
                    className={TEXTAREA_CLASS}
                  />
                </FormField>
              </div>
            </fieldset>

            <fieldset
              disabled={disabled}
              className="rounded-3xl border border-brand-gray10/20 bg-white/75 p-6 shadow-formal lg:p-8"
            >
              <legend className="px-3 font-display text-3xl text-brand-ink">Фотография</legend>
              <div className="mt-8 grid gap-5">
                <div className="grid gap-2">
                  <label htmlFor="photo" className="text-sm font-semibold uppercase tracking-[0.12em] text-brand-ink">
                    Фотография<span aria-hidden="true" className="text-brand-red"> *</span>
                  </label>
                  <input
                    id="photo"
                    name="photo"
                    type="file"
                    required
                    accept="image/jpeg,image/png,image/webp"
                    className={`${FIELD_CLASS} py-2`}
                  />
                </div>
                <p className={HELP_CLASS}>JPG, PNG или WebP. Фотография обрабатывается приватно и не публикуется.</p>
              </div>
            </fieldset>

            <fieldset
              disabled={disabled}
              className="rounded-3xl border border-brand-gray10/20 bg-white/75 p-6 shadow-formal lg:p-8"
            >
              <legend className="px-3 font-display text-3xl text-brand-ink">Согласия</legend>
              <div className="mt-8 space-y-4">
                <ConsentRow id="personal_data_processing" name="personal_data_processing">
                  <span>
                    <Link to="/consent" className="text-brand-red underline decoration-brand-red/40 underline-offset-2">
                      Согласен(на) на обработку персональных данных
                    </Link>
                  </span>
                </ConsentRow>

                <ConsentRow id="privacy_policy_acknowledgement" name="privacy_policy_acknowledgement">
                  <span>
                    <Link to="/privacy" className="text-brand-red underline decoration-brand-red/40 underline-offset-2">
                      Ознакомлен(а) с политикой конфиденциальности
                    </Link>
                  </span>
                </ConsentRow>

                <ConsentRow id="saint_petersburg_acknowledgement" name="saint_petersburg_acknowledgement">
                  {ST_PETERSBURG_COPY}
                </ConsentRow>
              </div>
            </fieldset>

            <div className="rounded-3xl border border-brand-gray10/20 bg-white/75 p-6 shadow-formal lg:p-8">
              <div
                role={submissionState === 'error' ? 'alert' : 'status'}
                aria-live="polite"
                className={`rounded-2xl border px-5 py-4 text-sm leading-6 ${
                  submissionState === 'error' ? STATUS_ERROR_CLASS : STATUS_SUCCESS_CLASS
                }`}
              >
                {feedback ?? (active ? 'Заполните все поля, прикрепите фотографию и отметьте все три согласия.' : INACTIVE_COPY)}
              </div>

              <div className="mt-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <p className={HELP_CLASS}>Перед отправкой проверьте данные, фотографию и все три согласия. Во время отправки повторное нажатие будет недоступно.</p>
                <button
                  type="submit"
                  disabled={disabled}
                  className="inline-flex items-center justify-center border border-brand-red bg-brand-red px-6 py-3 text-sm font-semibold uppercase tracking-[0.08em] text-white transition hover:bg-transparent hover:text-brand-red focus:outline focus:outline-2 focus:outline-offset-4 focus:outline-brand-red disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submissionState === 'submitting'
                    ? 'Отправка…'
                    : active
                      ? 'Отправить заявку'
                      : 'Приём заявок временно недоступен'}
                </button>
              </div>
            </div>
          </form>
        </div>
      </Section>
    </>
  );
}

type FormFieldProps = {
  id: string;
  label: string;
  required?: boolean;
  help?: string;
  className?: string;
  children: ReactNode;
};

function FormField({ id, label, required = false, help, className = '', children }: FormFieldProps) {
  return (
    <div className={`grid gap-2 ${className}`}>
      <label htmlFor={id} className="text-sm font-semibold uppercase tracking-[0.12em] text-brand-ink">
        {label}
        {required ? <span aria-hidden="true" className="text-brand-red"> *</span> : null}
      </label>
      {children}
      {help ? <p className={HELP_CLASS}>{help}</p> : null}
    </div>
  );
}

type ConsentRowProps = {
  id: string;
  name: string;
  children: ReactNode;
};

function ConsentRow({ id, name, children }: ConsentRowProps) {
  return (
    <div className="flex gap-3 rounded-2xl border border-brand-gray10/15 bg-white px-4 py-4">
      <input
        id={id}
        name={name}
        type="checkbox"
        value="true"
        required
        className="mt-1 h-4 w-4 shrink-0 accent-brand-red"
      />
      <label htmlFor={id} className="text-sm leading-6 text-brand-ink/80">
        {children}
      </label>
    </div>
  );
}

function formatCandidateSubmissionError(error: unknown): string {
  if (error instanceof CandidateApiError) {
    switch (error.status) {
      case 400:
      case 422:
        return VALIDATION_COPY;
      case 404:
        return UNAVAILABLE_COPY;
      case 413:
        return TOO_LARGE_COPY;
      case 429:
        return TOO_MANY_COPY;
      case 503:
        return TEMPORARY_COPY;
      default:
        return TEMPORARY_COPY;
    }
  }

  return NETWORK_COPY;
}
